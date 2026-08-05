from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.subscription_invoice import SubscriptionInvoice


class InvoiceLineItem(UUIDTimestampMixin, Base):
    """A single line item on a SubscriptionInvoice.

    ``kind`` is one of ``flat`` | ``overage_delivery_tasks`` |
    ``overage_route_optimizations``.
    """

    __tablename__ = 'invoice_line_items'

    invoice_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('subscription_invoices.id', ondelete='CASCADE'), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price_etb: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    amount_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invoice: Mapped[SubscriptionInvoice] = relationship(back_populates='lines')
