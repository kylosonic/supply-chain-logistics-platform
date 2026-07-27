from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ReplenishmentPlanStatus(StrEnum):
    PENDING_APPROVAL = 'pending_approval'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class ReplenishmentGenerateRequest(BaseModel):
    horizon_weeks: int = Field(default=4, ge=1, le=12)


class ReplenishmentApproveRequest(BaseModel):
    approved_quantity: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=255)


class ReplenishmentRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=255)


class ReplenishmentPlanRead(ORMBase):
    warehouse_code: str
    sku: str
    horizon_weeks: int
    avg_weekly_demand: float
    suggested_quantity: int
    approved_quantity: int | None
    status: ReplenishmentPlanStatus
    rationale: str
    created_by_user_id: str
    approved_by_user_id: str | None
    approved_at: datetime | None
    rejection_reason: str | None
