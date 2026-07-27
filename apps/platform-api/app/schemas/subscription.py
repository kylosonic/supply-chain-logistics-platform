from datetime import datetime

from pydantic import BaseModel

from app.schemas.auth import SubscriptionStatus, SubscriptionTier


class PlanRead(BaseModel):
    tier: SubscriptionTier
    title: str
    monthly_price_usd: int | None
    seat_limit: int | None
    vehicle_limit: int | None
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
