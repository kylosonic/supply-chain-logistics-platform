from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class CashCollection(UUIDTimestampMixin, Base):
    """Cash expected at the door, and whether it came back (NB-86).

    The platform already reconciled bank transfers against invoices
    (``payment_receipts`` -> ``wallet_credits``). In this market a driver also
    collects cash on delivery, and nothing recorded how much was expected, how
    much was handed in at the end of the day, or what was missing. That is the
    largest unmonitored cash risk an operator carries.

    Lifecycle (mirrors the reversal contract on ``payment_receipts``):

    - ``outstanding`` — goods delivered, cash still with the driver
    - ``collected``   — the driver has declared the amount they hold
    - ``settled``     — an office user has received the cash and closed the record
    - ``voided``      — the delivery was reversed; the debt is cancelled

    ``shortfall_etb`` is stored rather than derived so the figure that was acted
    on is preserved: if ``expected_etb`` were later corrected, a historic
    shortfall must not silently change.
    """

    __tablename__ = 'cash_collections'
    __table_args__ = (
        # A replayed confirmation over a flaky connection must update the row it
        # already created, never open a second one for the same shipment.
        UniqueConstraint('shipment_id', name='uq_cash_collections_shipment'),
        CheckConstraint('expected_etb >= 0', name='ck_cash_collections_expected_non_negative'),
        CheckConstraint('collected_etb >= 0', name='ck_cash_collections_collected_non_negative'),
        CheckConstraint('shortfall_etb >= 0', name='ck_cash_collections_shortfall_non_negative'),
        CheckConstraint(
            "status IN ('outstanding','collected','settled','voided')",
            name='ck_cash_collections_status',
        ),
        Index('ix_cash_collections_org_status', 'organization_id', 'status'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True
    )
    shipment_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False, index=True
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True, index=True
    )
    expected_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal('0'), nullable=False)
    collected_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal('0'), nullable=False)
    shortfall_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal('0'), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default='outstanding', nullable=False)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_by_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
