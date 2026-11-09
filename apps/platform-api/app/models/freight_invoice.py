from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class FreightInvoice(UUIDTimestampMixin, Base):
    __tablename__ = 'freight_invoices'

    # tenant scoping. Nullable for legacy rows created
    # before org scoping; backfilled in migration 20260811_0019.
    organization_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True
    )
    order_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('historical_orders.id', ondelete='CASCADE'), index=True, nullable=False)
    carrier_id: Mapped[str] = mapped_column(String(128), nullable=False)
    quoted_rate: Mapped[float] = mapped_column(Float, nullable=False)
    actual_rate: Mapped[float] = mapped_column(Float, nullable=False)
    variance: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default='matched', nullable=False)

    order = relationship('HistoricalOrder')
