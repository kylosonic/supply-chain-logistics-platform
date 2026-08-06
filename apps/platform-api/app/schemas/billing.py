from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WorkspacePhase(StrEnum):
    FREE = 'free'
    TRIAL = 'trial'
    LIMBO = 'limbo'
    ACTIVE = 'active'
    GRACE = 'grace'
    HARD_LOCKED = 'hard_locked'


class BillingCycle(StrEnum):
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'


class DesignatedAccountRead(BaseModel):
    bank_name: str
    bank_code: str
    account_holder: str
    account_number: str

    model_config = {'from_attributes': True}


class InvoiceLineRead(BaseModel):
    kind: str
    description: str
    quantity: int | None = None
    unit_price_etb: Decimal | None = None
    amount_etb: Decimal

    model_config = {'from_attributes': True}


class SubscriptionInvoiceRead(BaseModel):
    invoice_number: str
    tier: str
    period_start: date = Field(validation_alias='billing_period_start')
    period_end: date = Field(validation_alias='billing_period_end')
    flat_amount_etb: Decimal
    total_etb: Decimal
    balance_remaining_etb: Decimal
    due_date: date
    grace_days: int
    grace_ends_at: date
    status: str
    lines: list[InvoiceLineRead]
    designated_account: DesignatedAccountRead

    model_config = {'from_attributes': True}


class WorkspaceStateRead(BaseModel):
    phase: WorkspacePhase
    can_write: bool
    billing_visible: bool
    banner_message: str | None = None
    due_date: date | None = None
    days_remaining: int | None = None
    trial_ends_at: datetime | None = None
    next_billing_period_start: date | None = None


class NotificationRead(BaseModel):
    id: str
    kind: str
    title: str
    message: str
    payload: dict | None = None
    expires_at: datetime
    dismissed_at: datetime | None = None

    model_config = {'from_attributes': True}

    @field_validator('id', mode='before')
    @classmethod
    def _coerce_id(cls, v):
        return str(v) if isinstance(v, UUID) else v
