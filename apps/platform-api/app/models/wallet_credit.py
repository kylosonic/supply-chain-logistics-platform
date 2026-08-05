from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.subscription_invoice import SubscriptionInvoice


class WalletCredit(UUIDTimestampMixin, Base):
    """Surplus ledger (TECH-09 / NB-09.2-9.3).

    Every credit traces to a verified receipt (RESTRICT); rows become
    ``applied`` FIFO when a later invoice is issued.
    """

    __tablename__ = 'wallet_credits'
    __table_args__ = (
        CheckConstraint('amount_etb > 0', name='ck_wallet_credit_amount_positive'),
        CheckConstraint("status IN ('available','applied','voided')", name='ck_wallet_credit_status'),
        Index('ix_wallet_credits_org_status', 'organization_id', 'status'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    receipt_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('payment_receipts.id', ondelete='RESTRICT'), nullable=False
    )
    amount_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default='available', nullable=False)
    applied_to_invoice_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('subscription_invoices.id', ondelete='SET NULL'), nullable=True
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    applied_to_invoice: Mapped[SubscriptionInvoice | None] = relationship(lazy='joined')
