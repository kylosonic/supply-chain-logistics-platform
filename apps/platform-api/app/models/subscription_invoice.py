from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.collection_account import CollectionAccount
    from app.models.invoice_line_item import InvoiceLineItem
    from app.models.payment_receipt import PaymentReceipt


class SubscriptionInvoice(UUIDTimestampMixin, Base):
    """A subscription invoice issued at a billing-period boundary.

    At-most-once per (organization, billing_period_start) via the unique
    constraint ``uq_subscription_invoice_org_period``; lazy issuance relies
    on it to survive concurrent guard evaluations.
    """

    __tablename__ = 'subscription_invoices'
    __table_args__ = (
        UniqueConstraint('organization_id', 'billing_period_start', name='uq_subscription_invoice_org_period'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    invoice_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(24), nullable=False)
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    flat_amount_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance_remaining_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False)
    grace_ends_at: Mapped[date] = mapped_column(Date, nullable=False)
    designated_account_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('collection_accounts.id', ondelete='RESTRICT'), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), default='issued', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lines: Mapped[list[InvoiceLineItem]] = relationship(
        back_populates='invoice', cascade='all, delete-orphan', lazy='selectin'
    )
    designated_account: Mapped[CollectionAccount] = relationship(lazy='joined')
    receipts: Mapped[list[PaymentReceipt]] = relationship(
        back_populates='invoice', passive_deletes=True
    )
