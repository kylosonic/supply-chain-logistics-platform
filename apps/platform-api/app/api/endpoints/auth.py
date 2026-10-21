import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.security import (
    get_current_membership,
    get_current_user,
    get_current_user_from_token,
    require_roles,
)
from app.core.config import settings
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.repositories import MembershipRepository
from app.schemas.auth import (
    CompanySignupRequest,
    CompanySignupResponse,
    OrganizationRead,
    OrganizationRole,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserRead,
    UserRole,
)
from app.services.activation import seeding
from app.services.audit import record_audit_event
from app.services.security import (
    create_access_token,
    create_access_token_for_org,
    hash_password,
    verify_password,
)

router = APIRouter()
optional_bearer_scheme = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)

_RATE_LOGIN = '10/minute'
_RATE_REGISTER = '5/minute'
_RATE_SIGNUP = '3/minute'

if settings.app_env in ('development', 'test'):
    _RATE_LOGIN = '10000/minute'
    _RATE_REGISTER = '10000/minute'
    _RATE_SIGNUP = '10000/minute'

_COOKIE_NAME = 'supply_chain_token'
_RESERVED_ORG_SLUGS = {'legacy-unassigned-data'}


def _set_auth_cookie(response: Response, token: str) -> None:
    secure = settings.app_env not in ('development', 'test')
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        secure=secure,
        samesite='strict',
        path='/',
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path='/')


def _slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug[:64] or 'company'


def _extract_domain(email: str) -> str:
    parts = email.split('@')
    if len(parts) != 2 or '.' not in parts[1]:
        raise HTTPException(status_code=400, detail='Invalid company email')
    return parts[1].strip().lower()


def _ensure_not_public_email(domain: str) -> None:
    if domain in settings.blocked_public_email_domains:
        raise HTTPException(status_code=400, detail='Please use your company email domain')


def _generate_unique_slug(db: Session, company_name: str) -> str:
    base = _slugify(company_name)
    candidate = base
    counter = 1
    while (
        candidate in _RESERVED_ORG_SLUGS
        or db.execute(select(Organization.id).where(Organization.slug == candidate)).first()
        is not None
    ):
        counter += 1
        suffix = f'-{counter}'
        candidate = f'{base[: max(1, 64 - len(suffix))]}{suffix}'
    return candidate


def _generate_unique_username(db: Session, email: str) -> str:
    local = email.split('@', 1)[0]
    base = re.sub(r'[^a-zA-Z0-9_\-.]', '_', local).strip('._-') or 'user'
    candidate = base[:64]
    while db.execute(select(User.id).where(User.username == candidate)).first() is not None:
        suffix = f'_{uuid4().hex[:6]}'
        candidate = f'{base[: max(1, 64 - len(suffix))]}{suffix}'
    return candidate


@router.post('/register', response_model=UserRead, status_code=201)
@limiter.limit(_RATE_REGISTER)
def register_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
):
    users_exist = db.execute(select(User.id).limit(1)).first() is not None
    actor_membership: OrganizationMembership | None = None

    if users_exist:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Admin authentication required',
            )

        actor = get_current_user_from_token(credentials.credentials, db)
        if actor.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')
        actor_membership = MembershipRepository(db).get_active_membership(actor.id)
        if actor_membership is None or actor_membership.role not in {
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Workspace owner or admin membership required',
            )
    elif settings.app_env not in ('development', 'test'):
        # The public company-signup flow is the only production bootstrap.
        # Never create an unaffiliated global admin on a fresh deployment.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Create the first workspace through company signup',
        )

    exists = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail='Username already exists')

    assigned_role = payload.role if users_exist else UserRole.ADMIN
    user = User(
        username=payload.username,
        email=payload.email.lower() if payload.email else None,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=assigned_role,
        is_active=True,
    )
    db.add(user)
    db.flush()

    if actor_membership is not None:
        organization_id = actor_membership.organization_id
        membership_role = {
            UserRole.ADMIN: OrganizationRole.ADMIN,
            UserRole.OPERATOR: OrganizationRole.OPERATOR,
            UserRole.VIEWER: OrganizationRole.VIEWER,
        }[assigned_role]
    else:
        # Development/test-only bootstrap. The new admin receives a real
        # workspace membership so it cannot become an org-less global reader.
        bootstrap_org = Organization(
            name=f'{payload.username} Workspace',
            slug=_generate_unique_slug(db, f'{payload.username} Workspace'),
            primary_email_domain=None,
            subscription_tier='free',
            subscription_status='active',
            billing_phase='free',
            is_active=True,
        )
        db.add(bootstrap_org)
        db.flush()
        organization_id = bootstrap_org.id
        membership_role = OrganizationRole.OWNER

    db.add(
        OrganizationMembership(
            organization_id=organization_id,
            user_id=user.id,
            role=membership_role.value,
            is_active=True,
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.post('/company-signup', response_model=CompanySignupResponse, status_code=201)
@limiter.limit(_RATE_SIGNUP)
def company_signup(
    payload: CompanySignupRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = payload.company_email.strip().lower()
    domain = _extract_domain(normalized_email)
    _ensure_not_public_email(domain)

    existing = db.execute(
        select(User).where(
            or_(
                User.email == normalized_email,
                User.username == normalized_email,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail='A user with this email already exists')

    org = Organization(
        name=payload.company_name,
        slug=_generate_unique_slug(db, payload.company_name),
        primary_email_domain=domain,
        subscription_tier='free',
        subscription_status='active',
        billing_phase='free',
        is_active=True,
    )
    db.add(org)
    db.flush()

    user = User(
        username=_generate_unique_username(db, normalized_email),
        email=normalized_email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role='owner',
        is_active=True,
    )
    db.add(membership)

    record_audit_event(
        db,
        event_type='workspace.created',
        entity_type='organization',
        entity_id=str(org.id),
        actor=user,
        organization_id=str(org.id),
        description=f'Created workspace {org.name}',
        payload={
            'organization_name': org.name,
            'subscription_tier': org.subscription_tier,
            'tier_preference': payload.subscription_tier,
            'owner_email': normalized_email,
        },
    )

    # NB-25: seed the fresh workspace from the shipped sample CSVs
    # (per-workspace; audit workspace.seeded_sample_data recorded inside).
    seeding.seed_workspace(db, org, user, now=datetime.now(UTC))
    db.commit()
    db.refresh(org)
    db.refresh(user)

    token = create_access_token_for_org(
        subject=str(user.id),
        role=UserRole(user.role),
        organization_id=str(org.id),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )

    _set_auth_cookie(response, token)

    return CompanySignupResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
        organization=OrganizationRead.model_validate(org),
    )


@router.post('/login', response_model=TokenResponse)
@limiter.limit(_RATE_LOGIN)
def login_user(payload: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    identifier = (payload.identifier or payload.username or '').strip().lower()
    user = db.execute(
        select(User).where(
            or_(
                User.username == identifier,
                User.email == identifier,
            )
        )
    ).scalar_one_or_none()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    token = create_access_token(
        subject=str(user.id),
        role=UserRole(user.role),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )

    _set_auth_cookie(response, token)

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
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    rows = db.execute(
        select(User)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .where(OrganizationMembership.organization_id == membership.organization_id)
        .where(OrganizationMembership.is_active.is_(True))
        .order_by(User.username)
    ).scalars().all()
    return rows


@router.post('/logout')
def logout(response: Response):
    _clear_auth_cookie(response)
    return {'detail': 'Logged out'}


@router.get('/token', response_model=TokenResponse)
def get_token_for_ws(
    current_user: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    token = create_access_token_for_org(
        subject=str(current_user.id),
        role=UserRole(current_user.role),
        organization_id=str(membership.organization_id),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    return TokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_token_expire_minutes * 60,
    )
