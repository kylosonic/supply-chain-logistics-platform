from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.repositories import MembershipRepository, UserRepository
from app.schemas.auth import OrganizationRole, UserRole
from app.services.activation import freecap
from app.services.authz import ensure_role
from app.services.billing import locks
from app.services.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)
_COOKIE_NAME = 'supply_chain_token'


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None = None,
    cookie_token: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> str | None:
    if credentials and credentials.credentials:
        return credentials.credentials
    return cookie_token


def get_current_user_from_token(token: str, db: Session) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Inactive or missing user')
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias=_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_token(credentials, cookie_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing authentication token')

    return get_current_user_from_token(token, db)


def require_roles(*allowed: UserRole):
    def checker(
        user: User = Depends(get_current_user),
        membership: OrganizationMembership = Depends(get_current_membership),
    ) -> User:
        # Effective tenant authority is the lower of the global account role
        # and the active membership role. A stale or malformed mismatch can
        # never widen access.
        rank = {'viewer': 1, 'operator': 2, 'admin': 3}
        membership_to_account = {
            'viewer': UserRole.VIEWER,
            'operator': UserRole.OPERATOR,
            'admin': UserRole.ADMIN,
            'owner': UserRole.ADMIN,
        }
        membership_role = membership_to_account.get(str(membership.role))
        if membership_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invalid organization role',
            )
        effective_rank = min(rank[str(user.role)], rank[str(membership_role)])
        effective_role = next(
            role for role, role_rank in rank.items() if role_rank == effective_rank
        )
        try:
            ensure_role(UserRole(effective_role), list(allowed))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        return user

    return checker


def get_current_membership(
    x_org_id: str | None = Header(default=None, alias='X-Organization-Id'),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMembership:
    membership = MembershipRepository(db).get_active_membership(user.id, org_id=x_org_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No active organization membership')
    organization = db.get(Organization, membership.organization_id)
    if organization is None or not organization.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Workspace is inactive')
    return membership


def get_optional_membership(
    x_org_id: str | None = Header(default=None, alias='X-Organization-Id'),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMembership | None:
    """Soft membership lookup for non-tenant contexts only.

    Business and write endpoints must use ``get_current_membership`` or
    ``require_writable_workspace``. A ``None`` result must never grant access
    to tenant data.
    """
    return MembershipRepository(db).get_active_membership(user.id, org_id=x_org_id)


def require_writable_workspace(
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> OrganizationMembership:
    """Write guard (blueprint §5 + Phase 4 decision #5).

    - Active membership is mandatory; an unaffiliated account cannot write.
    - Load the org, run ``locks.assert_workspace_writable`` (phase check +
      Free-tier meter gate; refreshes workspace state incl. lazy invoice
      issuance) and raise ``423 Locked`` when either lock holds.
    - Phase lock wins the banner priority; the 423 detail gains
      ``free_cap_locked`` + ``free_cap_message`` when the Free cap holds.
    - Phases free/trial/active + under-cap -> membership returned unchanged.
    """
    try:
        locks.assert_workspace_writable(db, membership, datetime.now(UTC))
    except locks.WorkspaceLockedError as exc:
        state = exc.state
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                'state': state.phase.value,
                'message': state.banner_message,
                'days_remaining': state.days_remaining,
                'can_write': False,
            },
        ) from exc
    except freecap.FreeCapLockedError as exc:
        cap_state = exc.state
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                'state': 'free_cap_locked',
                'message': cap_state.message,
                'days_remaining': None,
                'can_write': False,
                'free_cap_locked': True,
                'free_cap_message': cap_state.message,
            },
        ) from exc
    return membership


def require_org_roles(*allowed: OrganizationRole):
    def checker(
        user: User = Depends(get_current_user),
        membership: OrganizationMembership = Depends(get_current_membership),
    ):
        account_rank = {'viewer': 1, 'operator': 2, 'admin': 3}
        membership_rank = {'viewer': 1, 'operator': 2, 'admin': 3, 'owner': 4}
        allowed_ranks = [membership_rank[str(role)] for role in allowed]
        if not allowed_ranks:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Insufficient organization permissions',
            )
        # The membership role cannot be weaker than the weakest allowed role,
        # and the account role remains a hard upper bound. This closes the
        # path where a workspace admin promoted a global viewer and then
        # relied on membership-only checks for privileged surfaces.
        required_rank = min(allowed_ranks)
        effective_rank = min(
            membership_rank.get(str(membership.role), 0),
            account_rank.get(str(user.role), 0),
        )
        if membership_rank.get(str(membership.role), 0) < required_rank or effective_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Insufficient organization permissions',
            )
        return membership

    return checker


# ---------------------------------------------------------------------------
# NB-64 — tenant scoping helpers (audit H-1)
# ---------------------------------------------------------------------------
# Implementation lives in ``app.core.tenant_scope`` so repositories can apply
# the same filter without importing this FastAPI dependency module (which would
# create a cycle via ``app.repositories``). Re-exported here because every
# endpoint already imports its security dependencies from this module.
from app.core.tenant_scope import (  # noqa: E402  (kept beside its consumers)
    actor_organization_id,
    order_by_organization_first,
    organization_scoped_get,
    resolve_scoped_organization,
    scoped_to_organization,
)

__all__ = [
    'actor_organization_id',
    'bearer_scheme',
    'get_current_membership',
    'get_current_user',
    'get_current_user_from_token',
    'get_optional_membership',
    'order_by_organization_first',
    'organization_scoped_get',
    'require_org_roles',
    'require_roles',
    'require_writable_workspace',
    'resolve_scoped_organization',
    'scoped_to_organization',
]
