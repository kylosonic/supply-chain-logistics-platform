"""Receipt processing schemas (TECH-07..17).

Standalone module: imports pydantic only. Cross-field validation that
depends on receipt state (escalation note, large-surplus 3-way) lives in
``services.billing.receipts.render_verdict``; pure shape constraints live
here.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ReceiptStatus(StrEnum):
    PENDING = 'pending'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    ESCALATED = 'escalated'


class Verdict(StrEnum):
    """Exact five-verdict enum (NB-15.1). There is NO amount-mismatch verdict."""

    VERIFY = 'verify'
    REJECT_WRONG_BANK = 'reject_wrong_bank'
    REJECT_DUPLICATE = 'reject_duplicate'
    REJECT_ILLEGIBLE = 'reject_illegible'
    ESCALATE = 'escalate'


class TrustedPayerAction(StrEnum):
    ADDED = 'added'
    VERIFIED_ONCE = 'verified_once'


class LargeSurplusDecision(StrEnum):
    CREDIT_FORWARD = 'credit_forward'
    CREDIT_BACKWARD = 'credit_backward'
    PARTIAL_IGNORE = 'partial_ignore'


class ReversalStatus(StrEnum):
    UNDO = 'undo'
    REVERSED = 'reversed'


class ReceiptUploadResponse(BaseModel):
    message: str
    receipt_id: str


class ReceiptRead(BaseModel):
    """Customer surface — no admin internals."""

    id: str
    status: ReceiptStatus
    verdict: Verdict | None = None
    invoice_number: str | None = None
    reference_number: str | None = None
    amount_etb: Decimal | None = None
    sender_name: str | None = None
    bank_code: str | None = None
    rejection_reason: str | None = None
    created_at: datetime
    decided_at: datetime | None = None
    reversal_status: ReversalStatus | None = None

    @field_validator('id', mode='before')
    @classmethod
    def _coerce_id(cls, v):
        return str(v) if isinstance(v, UUID) else v


class ReceiptQueueItemRead(BaseModel):
    """Admin verification-queue surface."""

    id: str
    organization_id: str
    organization_name: str
    invoice_number: str | None = None
    designated_bank_code: str | None = None
    status: ReceiptStatus
    verdict: Verdict | None = None
    extracted_fields: dict[str, str | None]
    confidence: dict[str, float]
    low_confidence_fields: list[str]
    is_new_sender: bool
    is_cash_sender: bool
    is_wrong_bank_within_portfolio: bool
    is_large_surplus: bool
    is_duplicate: bool
    has_zero_confidence: bool
    zero_confidence_warning: str | None = None
    recommended_verdict: Verdict | None = None
    surplus_etb: Decimal | None = None
    large_surplus_decision: LargeSurplusDecision | None = None
    partial_credit_amount_etb: Decimal | None = None
    trusted_payer_action: TrustedPayerAction | None = None
    admin_note: str | None = None
    sender_has_reversed_credit: bool = False
    fraud_risk_since: datetime | None = None
    dispute_text: str | None = None
    dispute_status: str | None = None
    file_name: str
    content_type: str
    file_size_bytes: int
    created_at: datetime

    @field_validator('id', 'organization_id', mode='before')
    @classmethod
    def _coerce_ids(cls, v):
        return str(v) if isinstance(v, UUID) else v


class VerdictRequest(BaseModel):
    verdict: Verdict
    note: str | None = Field(default=None, max_length=512)
    admin_note: str | None = Field(default=None, max_length=512)
    trusted_payer_action: TrustedPayerAction | None = None
    large_surplus_decision: LargeSurplusDecision | None = None
    partial_credit_amount_etb: Decimal | None = None

    @model_validator(mode='after')
    def _validate_shape(self) -> 'VerdictRequest':
        if self.partial_credit_amount_etb is not None and self.partial_credit_amount_etb <= 0:
            raise ValueError('partial_credit_amount_etb must be positive')
        if self.partial_credit_amount_etb is not None and self.large_surplus_decision != LargeSurplusDecision.PARTIAL_IGNORE:
            raise ValueError('partial_credit_amount_etb is only valid with large_surplus_decision=partial_ignore')
        return self


class DisputeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)

    @field_validator('text')
    @classmethod
    def _reject_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('dispute text must not be blank')
        return stripped


class WalletCreditRead(BaseModel):
    amount_etb: Decimal
    status: str
    applied_to_invoice_number: str | None = None
    created_at: datetime


class WalletRead(BaseModel):
    available_etb: Decimal
    credits: list[WalletCreditRead]


class UndoRequest(BaseModel):
    """Silent Undo (NB-19): optional note, max 512 chars."""

    note: str | None = Field(default=None, max_length=512)


class ReverseRequest(BaseModel):
    """Explicit Reverse (NB-20): MANDATORY non-blank reason (NB-20.2)."""

    reason: str = Field(min_length=1, max_length=512)

    @field_validator('reason')
    @classmethod
    def _reject_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('reverse reason must not be blank')
        return stripped


class ReversalRead(BaseModel):
    """The admin reversal outcome (message populated on Reverse with the
    exact NB-20.3 copy)."""

    receipt_id: str
    invoice_number: str | None = None
    reference_number: str | None = None
    amount_etb: Decimal | None = None
    reversal_status: ReversalStatus
    reversal_note: str | None = None
    reversed_at: datetime | None = None
    restored_balance_etb: Decimal | None = None
    wallet_voided_etb: Decimal | None = None
    message: str | None = None

    @field_validator('receipt_id', mode='before')
    @classmethod
    def _coerce_id(cls, v):
        return str(v) if isinstance(v, UUID) else v


class VerifiedReceiptAuditRead(BaseModel):
    """One row of GET /receipts/audit — availability computed SERVER-side
    (decision #7)."""

    id: str
    organization_id: str
    organization_name: str
    invoice_number: str | None = None
    reference_number: str | None = None
    amount_etb: Decimal | None = None
    sender_name: str | None = None
    decided_at: datetime | None = None
    reversal_status: ReversalStatus | None = None
    undo_available: bool
    undo_available_until: datetime | None = None
    reverse_available: bool

    @field_validator('id', 'organization_id', mode='before')
    @classmethod
    def _coerce_ids(cls, v):
        return str(v) if isinstance(v, UUID) else v


class ReceiptAuditEventRead(BaseModel):
    """One audit event of the per-receipt timeline (NB-18.1)."""

    id: str
    event_type: str
    description: str
    created_at: datetime
    payload: dict | list | None = None
    available_actions: list[str] = []
