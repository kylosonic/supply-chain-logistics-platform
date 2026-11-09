from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    LargeBinary,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.subscription_invoice import SubscriptionInvoice


class PaymentReceipt(UUIDTimestampMixin, Base):
    """One row per uploaded receipt file (TECH-07..17).

    Status ladder: pending -> verified | rejected | escalated. The
    reference number is the system-wide dedup key: the partial unique
    index below enforces at-most-one VERIFIED receipt per reference.
    """

    __tablename__ = 'payment_receipts'
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','verified','rejected','escalated')",
            name='ck_payment_receipt_status',
        ),
        CheckConstraint(
            "verdict IN ('verify','reject_wrong_bank','reject_duplicate','reject_illegible','escalate') "
            'OR verdict IS NULL',
            name='ck_payment_receipt_verdict',
        ),
        CheckConstraint(
            "trusted_payer_action IN ('added','verified_once') OR trusted_payer_action IS NULL",
            name='ck_payment_receipt_trusted_payer_action',
        ),
        CheckConstraint(
            "large_surplus_decision IN ('credit_forward','credit_backward','partial_ignore') "
            'OR large_surplus_decision IS NULL',
            name='ck_payment_receipt_large_surplus_decision',
        ),
        CheckConstraint(
            "reversal_status IN ('undo','reversed') OR reversal_status IS NULL",
            name='ck_payment_receipt_reversal_status',
        ),
        Index('ix_payment_receipts_org_status', 'organization_id', 'status'),
        Index('ix_payment_receipts_status_created', 'status', 'created_at'),
        Index(
            'uq_payment_receipt_verified_ref',
            'reference_number',
            unique=True,
            postgresql_where=text("status = 'verified'"),
            sqlite_where=text("status = 'verified'"),
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    invoice_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('subscription_invoices.id', ondelete='SET NULL'), index=True, nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    reference_number: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    amount_etb: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    sender_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sender_account_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_account_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transfer_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bank_code: Mapped[str | None] = mapped_column(String(16), nullable=True)

    status: Mapped[str] = mapped_column(String(24), default='pending', nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(24), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    decision_made_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trusted_payer_action: Mapped[str | None] = mapped_column(String(24), nullable=True)
    large_surplus_decision: Mapped[str | None] = mapped_column(String(24), nullable=True)
    partial_credit_amount_etb: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    surplus_etb: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    # Reversal layer (decision #2): the receipt NEVER leaves status='verified';
    # these columns carry the correction. One reversal per receipt, ever.
    reversal_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reversal_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reversed_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_new_sender: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cash_sender: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_wrong_bank_within_portfolio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_large_surplus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_zero_confidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    low_confidence_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)

    invoice: Mapped[SubscriptionInvoice | None] = relationship(
        back_populates='receipts', lazy='joined'
    )
