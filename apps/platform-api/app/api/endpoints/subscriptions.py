from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, require_org_roles
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.usage_meter import OrganizationUsageCounter
from app.schemas.auth import OrganizationRole, SubscriptionTier
from app.schemas.subscription import (
    PlanRead,
    PlanThresholdEvent,
    SelectTierRequest,
    SubscriptionRead,
    ThresholdLevel,
    UsageMeterRead,
    UsageMeterRecordRequest,
    UsageMetric,
    UsageRecordResponse,
)
from app.services.audit import record_audit_event
from app.services.metering import current_usage_window

router = APIRouter()

PLAN_QUOTAS: dict[str, dict[str, tuple[int | None, float | None]]] = {
    'starter': {
        UsageMetric.DELIVERY_TASKS: (2500, 0.2),
        UsageMetric.ROUTE_OPTIMIZATIONS: (50, 1.5),
    },
    'scale': {
        UsageMetric.DELIVERY_TASKS: (5000, 0.16),
        UsageMetric.ROUTE_OPTIMIZATIONS: (250, 1.0),
    },
    'enterprise': {
        UsageMetric.DELIVERY_TASKS: (None, None),
        UsageMetric.ROUTE_OPTIMIZATIONS: (None, None),
    },
}

PLANS: list[PlanRead] = [
    PlanRead(
        tier='starter',
        title='Starter',
        monthly_price_usd=399,
        seat_limit=3,
        vehicle_limit=25,
        included_tasks_per_month=PLAN_QUOTAS['starter'][UsageMetric.DELIVERY_TASKS][0],
        overage_unit_price_usd=PLAN_QUOTAS['starter'][UsageMetric.DELIVERY_TASKS][1],
        includes_sso=False,
        includes_priority_support=False,
    ),
    PlanRead(
        tier='scale',
        title='Scale',
        monthly_price_usd=1290,
        seat_limit=20,
        vehicle_limit=250,
        included_tasks_per_month=PLAN_QUOTAS['scale'][UsageMetric.DELIVERY_TASKS][0],
        overage_unit_price_usd=PLAN_QUOTAS['scale'][UsageMetric.DELIVERY_TASKS][1],
        includes_sso=True,
        includes_priority_support=True,
    ),
    PlanRead(
        tier='enterprise',
        title='Enterprise',
        monthly_price_usd=None,
        seat_limit=None,
        vehicle_limit=None,
        included_tasks_per_month=PLAN_QUOTAS['enterprise'][UsageMetric.DELIVERY_TASKS][0],
        overage_unit_price_usd=PLAN_QUOTAS['enterprise'][UsageMetric.DELIVERY_TASKS][1],
        includes_sso=True,
        includes_priority_support=True,
    ),
]


def _current_usage_window(reference_day: date) -> tuple[date, date]:
    return current_usage_window(reference_day)


def _usage_utilization_percent(used_units: int, included_units: int | None) -> int | None:
    if not included_units or included_units <= 0:
        return None
    return int(round((used_units / included_units) * 100))


def _usage_read(
    counter: OrganizationUsageCounter,
    included_units: int | None,
    overage_unit_price_usd: float | None,
) -> UsageMeterRead:
    overage_units = 0
    estimated_overage_cost_usd = None
    if included_units is not None:
        overage_units = max(counter.used_units - included_units, 0)
        if overage_unit_price_usd is not None:
            estimated_overage_cost_usd = round(overage_units * overage_unit_price_usd, 2)

    return UsageMeterRead(
        metric=counter.metric,
        period_start=counter.period_start,
        period_end=counter.period_end,
        included_units=included_units,
        used_units=counter.used_units,
        overage_units=overage_units,
        utilization_percent=_usage_utilization_percent(counter.used_units, included_units),
        estimated_overage_cost_usd=estimated_overage_cost_usd,
    )


def _build_threshold_events(
    *,
    metric: UsageMetric,
    tier: str,
    included_units: int | None,
    before_units: int,
    after_units: int,
) -> list[PlanThresholdEvent]:
    if not included_units:
        return []

    try:
        tier_value = SubscriptionTier(tier)
    except ValueError:
        return []
    events: list[PlanThresholdEvent] = []

    approaching_mark = max(1, int(included_units * 0.8))
    if before_units < approaching_mark <= after_units:
        events.append(
            PlanThresholdEvent(
                metric=metric,
                tier=tier_value,
                level=ThresholdLevel.APPROACHING_LIMIT,
                usage_units=after_units,
                included_units=included_units,
                utilization_percent=_usage_utilization_percent(after_units, included_units) or 0,
                message='Usage crossed 80% of included monthly capacity.',
            )
        )

    if before_units < included_units <= after_units:
        events.append(
            PlanThresholdEvent(
                metric=metric,
                tier=tier_value,
                level=ThresholdLevel.LIMIT_REACHED,
                usage_units=after_units,
                included_units=included_units,
                utilization_percent=_usage_utilization_percent(after_units, included_units) or 0,
                message='Included monthly capacity has been fully consumed.',
            )
        )

    if before_units <= included_units < after_units:
        events.append(
            PlanThresholdEvent(
                metric=metric,
                tier=tier_value,
                level=ThresholdLevel.OVERAGE,
                usage_units=after_units,
                included_units=included_units,
                utilization_percent=_usage_utilization_percent(after_units, included_units) or 0,
                message='Overage usage is now active for this period.',
            )
        )

    return events


def _plan_quota_for_tier(tier: str, metric: str) -> tuple[int | None, float | None]:
    return PLAN_QUOTAS.get(tier, {}).get(metric, (None, None))


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


@router.get('/usage/me', response_model=UsageMeterRead)
def get_my_usage(
    metric: UsageMetric = Query(default=UsageMetric.DELIVERY_TASKS),
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    period_start, period_end = _current_usage_window(datetime.now(UTC).date())
    counter = db.execute(
        select(OrganizationUsageCounter).where(
            OrganizationUsageCounter.organization_id == organization.id,
            OrganizationUsageCounter.metric == metric,
            OrganizationUsageCounter.period_start == period_start,
        )
    ).scalar_one_or_none()

    if not counter:
        counter = OrganizationUsageCounter(
            organization_id=organization.id,
            metric=metric,
            period_start=period_start,
            period_end=period_end,
            used_units=0,
        )

    included_units, overage_rate = _plan_quota_for_tier(organization.subscription_tier, metric)
    return _usage_read(counter, included_units, overage_rate)


@router.post('/usage/record', response_model=UsageRecordResponse)
def record_usage(
    payload: UsageMeterRecordRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.OPERATOR)
    ),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    occurred_at = payload.occurred_at
    if occurred_at is None:
        reference_day = datetime.now(UTC).date()
    else:
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        else:
            occurred_at = occurred_at.astimezone(UTC)
        reference_day = occurred_at.date()

    period_start, period_end = _current_usage_window(reference_day)

    counter = db.execute(
        select(OrganizationUsageCounter).where(
            OrganizationUsageCounter.organization_id == organization.id,
            OrganizationUsageCounter.metric == payload.metric,
            OrganizationUsageCounter.period_start == period_start,
        )
    ).scalar_one_or_none()

    if not counter:
        counter = OrganizationUsageCounter(
            organization_id=organization.id,
            metric=payload.metric,
            period_start=period_start,
            period_end=period_end,
            used_units=0,
        )
        db.add(counter)

    before_units = counter.used_units
    counter.used_units += payload.units
    counter.period_end = period_end
    counter.updated_at = datetime.now(UTC)

    db.add(counter)
    db.commit()
    db.refresh(counter)

    included_units, overage_rate = _plan_quota_for_tier(organization.subscription_tier, payload.metric)
    events = _build_threshold_events(
        metric=payload.metric,
        tier=organization.subscription_tier,
        included_units=included_units,
        before_units=before_units,
        after_units=counter.used_units,
    )

    return UsageRecordResponse(
        usage=_usage_read(counter, included_units, overage_rate),
        events=events,
    )


@router.post('/select-tier', response_model=SubscriptionRead)
def select_tier(
    payload: SelectTierRequest,
    db: Session = Depends(get_db),
    membership_user: OrganizationMembership = Depends(require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)),
):
    organization = db.get(Organization, membership_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    previous_tier = organization.subscription_tier
    organization.subscription_tier = payload.tier
    if organization.subscription_status in {'trialing', 'past_due'}:
        organization.subscription_status = 'active'
    organization.updated_at = datetime.now(UTC)

    db.add(organization)

    record_audit_event(
        db,
        event_type='subscription.tier_selected',
        entity_type='organization',
        entity_id=organization.id,
        organization_id=membership_user.organization_id,
        description=f'Changed subscription tier from {previous_tier} to {payload.tier}',
        payload={'from_tier': previous_tier, 'to_tier': payload.tier},
    )
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
