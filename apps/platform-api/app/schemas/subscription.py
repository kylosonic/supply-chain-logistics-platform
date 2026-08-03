from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import SubscriptionStatus, SubscriptionTier


class PlanRead(BaseModel):
    tier: SubscriptionTier
    title: str
    monthly_price_usd: int | None
    seat_limit: int | None
    vehicle_limit: int | None
    included_tasks_per_month: int | None
    overage_unit_price_usd: float | None
    includes_sso: bool
    includes_priority_support: bool


class SelectTierRequest(BaseModel):
    tier: SubscriptionTier


class SubscriptionRead(BaseModel):
    organization_id: str
    organization_name: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    preferred_ai_provider: str | None = None
    preferred_ai_key_id: str | None = None
    updated_at: datetime | None

    model_config = {'from_attributes': True}

    @field_validator('organization_id', 'preferred_ai_key_id', mode='before')
    @classmethod
    def _coerce_ids(cls, v):
        return str(v) if isinstance(v, UUID) else v


class UsageMetric(StrEnum):
    DELIVERY_TASKS = 'delivery_tasks'
    ROUTE_OPTIMIZATIONS = 'route_optimizations'


class ThresholdLevel(StrEnum):
    APPROACHING_LIMIT = 'approaching_limit'
    LIMIT_REACHED = 'limit_reached'
    OVERAGE = 'overage'


class UsageMeterRecordRequest(BaseModel):
    metric: UsageMetric = UsageMetric.DELIVERY_TASKS
    units: int = Field(default=1, ge=1, le=1_000_000)
    occurred_at: datetime | None = None


class UsageMeterRead(BaseModel):
    metric: UsageMetric
    period_start: date
    period_end: date
    included_units: int | None
    used_units: int
    overage_units: int
    utilization_percent: int | None
    estimated_overage_cost_usd: float | None


class PlanThresholdEvent(BaseModel):
    metric: UsageMetric
    tier: SubscriptionTier
    level: ThresholdLevel
    usage_units: int
    included_units: int
    utilization_percent: int
    message: str


class UsageRecordResponse(BaseModel):
    usage: UsageMeterRead
    events: list[PlanThresholdEvent]
