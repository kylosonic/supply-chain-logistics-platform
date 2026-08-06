from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class HistoricalOrder(UUIDTimestampMixin, Base):
    __tablename__ = 'historical_orders'
    __table_args__ = (
        CheckConstraint("data_origin IN ('sample', 'real')", name='ck_historical_orders_data_origin'),
    )

    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    data_origin: Mapped[str] = mapped_column(
        String(8), default='real', server_default='real', nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    customer_region: Mapped[str] = mapped_column(String(64), default='unknown', nullable=False)
    weather_avg_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_precip_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_disruption_index: Mapped[float | None] = mapped_column(Float, nullable=True)

    warehouse = relationship('Warehouse', back_populates='orders')
    item = relationship('Item', back_populates='orders')
