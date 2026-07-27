from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, require_org_roles
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.schemas.auth import OrganizationRole
from app.schemas.subscription import PlanRead, SelectTierRequest, SubscriptionRead

router = APIRouter()

PLANS: list[PlanRead] = [
    PlanRead(
        tier='starter',
        title='Starter',
        monthly_price_usd=399,
        seat_limit=3,
        vehicle_limit=25,
        includes_sso=False,
        includes_priority_support=False,
    ),
    PlanRead(
        tier='scale',
        title='Scale',
        monthly_price_usd=1290,
        seat_limit=20,
        vehicle_limit=250,
        includes_sso=True,
        includes_priority_support=True,
    ),
    PlanRead(
        tier='enterprise',
        title='Enterprise',
        monthly_price_usd=None,
        seat_limit=None,
        vehicle_limit=None,
        includes_sso=True,
        includes_priority_support=True,
    ),
]


@router.get('/plans', response_model=list[PlanRead])
def list_plans() -> list[PlanRead]:
    return PLANS


@router.get('/me', response_model=SubscriptionRead)
def get_my_subscription(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    return SubscriptionRead(
        organization_id=organization.id,
        organization_name=organization.name,
        tier=organization.subscription_tier,
        status=organization.subscription_status,
        preferred_ai_provider=organization.preferred_ai_provider,
        preferred_ai_key_id=organization.preferred_ai_key_id,
        updated_at=organization.updated_at,
    )


@router.post('/select-tier', response_model=SubscriptionRead)
def select_tier(
    payload: SelectTierRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    organization.subscription_tier = payload.tier
    if organization.subscription_status in {'trialing', 'past_due'}:
        organization.subscription_status = 'active'
    organization.updated_at = datetime.now(UTC)

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return SubscriptionRead(
        organization_id=organization.id,
        organization_name=organization.name,
        tier=organization.subscription_tier,
        status=organization.subscription_status,
        preferred_ai_provider=organization.preferred_ai_provider,
        preferred_ai_key_id=organization.preferred_ai_key_id,
        updated_at=organization.updated_at,
    )
