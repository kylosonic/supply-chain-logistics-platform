from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.security import require_org_roles, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.organization_invitation import OrganizationInvitation
from app.models.user import User
from app.schemas.auth import OrganizationRead, OrganizationRole, UserRead, UserRole
from app.schemas.team import (
    InvitationAccept,
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationCreated,
    InvitationRead,
    MemberRoleUpdate,
    OrganizationMemberRead,
)
from app.services.audit import record_audit_event
from app.services.security import (
    create_access_token_for_org,
    hash_password,
    verify_password,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_INVITATION_TTL_HOURS = 72
_ROLE_RANK = {'viewer': 1, 'operator': 2, 'admin': 3}
_ACCEPT_RATE = '10/minute'
if settings.app_env in ('development', 'test'):
    _ACCEPT_RATE = '10000/minute'


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _require_owner_or_admin(
    membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
) -> OrganizationMembership:
    return membership


def _member_read(membership: OrganizationMembership, user: User) -> OrganizationMemberRead:
    return OrganizationMemberRead(
        membership_id=str(membership.id),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


@router.get('/members', response_model=list[OrganizationMemberRead])
def list_members(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(_require_owner_or_admin),
):
    rows = db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(OrganizationMembership.organization_id == membership.organization_id)
        .order_by(User.username)
    ).all()
    return [_member_read(member, user) for member, user in rows]


@router.get('/invitations', response_model=list[InvitationRead])
def list_invitations(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(_require_owner_or_admin),
):
    return (
        db.execute(
            select(OrganizationInvitation)
            .where(OrganizationInvitation.organization_id == membership.organization_id)
            .order_by(OrganizationInvitation.created_at.desc())
        )
        .scalars()
        .all()
    )


@router.post('/invitations', response_model=InvitationCreated, status_code=201)
def create_invitation(
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(_require_owner_or_admin),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
):
    existing_user = db.execute(
        select(User).where(func.lower(User.email) == payload.email)
    ).scalar_one_or_none()
    if existing_user is not None:
        existing_membership = db.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.user_id == existing_user.id,
                OrganizationMembership.organization_id == membership.organization_id,
                OrganizationMembership.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if existing_membership is not None:
            raise HTTPException(status_code=409, detail='This person is already in the workspace')
        if _ROLE_RANK[payload.role.value] > _ROLE_RANK.get(str(existing_user.role), 0):
            raise HTTPException(
                status_code=409,
                detail='The existing account role is lower than the invited role',
            )

    pending = db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == membership.organization_id,
            OrganizationInvitation.email == payload.email,
            OrganizationInvitation.status == 'pending',
            OrganizationInvitation.expires_at > datetime.now(UTC),
        )
    ).scalar_one_or_none()
    if pending is not None:
        raise HTTPException(status_code=409, detail='An active invitation already exists for this email')

    token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation(
        organization_id=membership.organization_id,
        email=payload.email,
        role=payload.role.value,
        token_hash=_hash_token(token),
        invited_by_user_id=actor.id,
        expires_at=datetime.now(UTC) + timedelta(hours=_INVITATION_TTL_HOURS),
        status='pending',
    )
    db.add(invitation)
    db.flush()
    record_audit_event(
        db,
        event_type='organization.member_invited',
        entity_type='organization_invitation',
        entity_id=str(invitation.id),
        actor=actor,
        organization_id=str(membership.organization_id),
        description=f'Invited {payload.email} as {payload.role.value}',
        payload={'email': payload.email, 'role': payload.role.value},
    )
    db.commit()
    db.refresh(invitation)
    invite_url = f'{settings.console_url.rstrip("/")}/accept-invite#token={token}'
    return InvitationCreated(
        invitation=InvitationRead.model_validate(invitation),
        token=token,
        invite_url=invite_url,
    )


@router.delete('/invitations/{invitation_id}', status_code=204)
def revoke_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(_require_owner_or_admin),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
):
    invitation = db.get(OrganizationInvitation, invitation_id)
    if invitation is None or invitation.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Invitation not found')
    if invitation.status != 'pending':
        raise HTTPException(status_code=409, detail='Only pending invitations can be revoked')
    invitation.status = 'revoked'
    record_audit_event(
        db,
        event_type='organization.invitation_revoked',
        entity_type='organization_invitation',
        entity_id=str(invitation.id),
        actor=actor,
        organization_id=str(membership.organization_id),
        description=f'Revoked invitation for {invitation.email}',
        payload={'email': invitation.email},
    )
    db.commit()


@router.post('/invitations/accept', response_model=InvitationAcceptResponse)
@limiter.limit(_ACCEPT_RATE)
def accept_invitation(
    payload: InvitationAccept,
    request: Request,
    db: Session = Depends(get_db),
):
    invitation = db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.token_hash == _hash_token(payload.token.strip()),
            OrganizationInvitation.status == 'pending',
        )
    ).scalar_one_or_none()
    if invitation is None or _utc(invitation.expires_at) <= datetime.now(UTC):
        raise HTTPException(status_code=410, detail='This invitation is invalid or expired')

    organization = db.get(Organization, invitation.organization_id)
    if organization is None or not organization.is_active:
        raise HTTPException(status_code=410, detail='This workspace is no longer active')

    user = db.execute(select(User).where(func.lower(User.email) == invitation.email)).scalar_one_or_none()
    if user is not None:
        if not user.is_active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail='Existing account password is incorrect')
        if _ROLE_RANK[invitation.role] > _ROLE_RANK.get(str(user.role), 0):
            raise HTTPException(
                status_code=409,
                detail='The existing account role is lower than the invited role',
            )
    else:
        username_exists = db.execute(select(User.id).where(User.username == payload.username)).first()
        if username_exists is not None:
            raise HTTPException(status_code=409, detail='Username already exists')
        user = User(
            username=payload.username,
            email=invitation.email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=UserRole(invitation.role),
            is_active=True,
        )
        db.add(user)
        db.flush()

    already_member = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == invitation.organization_id,
            OrganizationMembership.user_id == user.id,
        )
    ).scalar_one_or_none()
    if already_member is not None:
        raise HTTPException(status_code=409, detail='This person is already in the workspace')

    membership = OrganizationMembership(
        organization_id=invitation.organization_id,
        user_id=user.id,
        role=invitation.role,
        is_active=True,
    )
    db.add(membership)
    invitation.status = 'accepted'
    invitation.accepted_at = datetime.now(UTC)
    invitation.accepted_by_user_id = user.id
    record_audit_event(
        db,
        event_type='organization.invitation_accepted',
        entity_type='organization_invitation',
        entity_id=str(invitation.id),
        actor=user,
        organization_id=str(invitation.organization_id),
        description=f'{user.username} accepted a workspace invitation',
        payload={'email': invitation.email, 'role': invitation.role},
    )
    db.commit()
    db.refresh(user)
    token = create_access_token_for_org(
        subject=str(user.id),
        role=UserRole(user.role),
        organization_id=str(organization.id),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    return InvitationAcceptResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
        organization=OrganizationRead.model_validate(organization),
        organization_role=membership.role,
    )


@router.patch('/members/{membership_id}', response_model=OrganizationMemberRead)
def update_member_role(
    membership_id: str,
    payload: MemberRoleUpdate,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(_require_owner_or_admin),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
):
    target = db.get(OrganizationMembership, membership_id)
    if target is None or target.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Member not found')
    if target.user_id == actor.id:
        raise HTTPException(status_code=409, detail='You cannot change your own role')
    if target.role == 'owner':
        raise HTTPException(status_code=403, detail='Ownership transfer is not supported')

    target.role = payload.role.value
    user = db.get(User, target.user_id)
    record_audit_event(
        db,
        event_type='organization.member_role_changed',
        entity_type='organization_membership',
        entity_id=str(target.id),
        actor=actor,
        organization_id=str(membership.organization_id),
        description=f'Changed {user.username} role to {target.role}' if user else 'Changed member role',
        payload={'role': target.role},
    )
    db.commit()
    db.refresh(target)
    if user is None:
        raise HTTPException(status_code=404, detail='Member user not found')
    return _member_read(target, user)


@router.delete('/members/{membership_id}', status_code=204)
def deactivate_member(
    membership_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(_require_owner_or_admin),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
):
    target = db.get(OrganizationMembership, membership_id)
    if target is None or target.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Member not found')
    if target.user_id == actor.id:
        raise HTTPException(status_code=409, detail='You cannot remove yourself')
    if target.role == 'owner':
        owner_count = db.execute(
            select(func.count(OrganizationMembership.id)).where(
                OrganizationMembership.organization_id == membership.organization_id,
                OrganizationMembership.role == 'owner',
                OrganizationMembership.is_active.is_(True),
            )
        ).scalar_one()
        if owner_count <= 1:
            raise HTTPException(status_code=409, detail='The last workspace owner cannot be removed')

    target.is_active = False
    user = db.get(User, target.user_id)
    record_audit_event(
        db,
        event_type='organization.member_deactivated',
        entity_type='organization_membership',
        entity_id=str(target.id),
        actor=actor,
        organization_id=str(membership.organization_id),
        description=f'Removed {user.username} from the workspace' if user else 'Removed member',
        payload={},
    )
    db.commit()
