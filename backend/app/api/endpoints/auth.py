from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import get_current_user, get_current_user_from_token, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead, UserRole
from app.services.security import create_access_token, hash_password, verify_password

router = APIRouter()
optional_bearer_scheme = HTTPBearer(auto_error=False)


@router.post('/register', response_model=UserRead, status_code=201)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
):
    users_exist = db.execute(select(User.id).limit(1)).first() is not None

    if users_exist:
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Admin authentication required')

        actor = get_current_user_from_token(credentials.credentials, db)
        if actor.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')

    exists = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail='Username already exists')

    assigned_role = payload.role if users_exist else UserRole.ADMIN
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=assigned_role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post('/login', response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    token = create_access_token(
        subject=user.id,
        role=UserRole(user.role),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )

    return TokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get('/me', response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get('/users', response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return db.execute(select(User).order_by(User.username)).scalars().all()
