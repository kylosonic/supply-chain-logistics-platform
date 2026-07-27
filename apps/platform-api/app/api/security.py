from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.schemas.auth import OrganizationRole, UserRole
from app.services.authz import ensure_role
from app.services.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_from_token(token: str, db: Session) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Inactive or missing user')
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')

    return get_current_user_from_token(credentials.credentials, db)


def require_roles(*allowed: UserRole):
    def checker(user: User = Depends(get_current_user)) -> User:
        try:
            ensure_role(UserRole(user.role), list(allowed))
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        return user

    return checker


def get_current_membership(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMembership:
    membership = db.execute(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.is_active.is_(True),
        )
        .order_by(OrganizationMembership.created_at.asc())
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No active organization membership')
    return membership


def require_org_roles(*allowed: OrganizationRole):
    def checker(membership: OrganizationMembership = Depends(get_current_membership)) -> OrganizationMembership:
        membership_role = OrganizationRole(membership.role)
        if membership_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient organization permissions')
        return membership

    return checker
