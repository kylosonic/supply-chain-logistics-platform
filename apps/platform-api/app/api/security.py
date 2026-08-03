from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.repositories import MembershipRepository, UserRepository
from app.schemas.auth import OrganizationRole, UserRole
from app.services.authz import ensure_role
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
    def checker(user: User = Depends(get_current_user)) -> User:
        try:
            ensure_role(UserRole(user.role), list(allowed))
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
    return membership


def require_org_roles(*allowed: OrganizationRole):
    def checker(membership=Depends(get_current_membership)):
        membership_role = OrganizationRole(membership.role)
        if membership_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient organization permissions')
        return membership

    return checker
