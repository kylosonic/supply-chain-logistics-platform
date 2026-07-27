from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class HistoricalOrder(UUIDTimestampMixin, Base):
    __tablename__ = 'historical_orders'

    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    customer_region: Mapped[str] = mapped_column(String(64), default='unknown', nullable=False)
    weather_avg_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_precip_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_disruption_index: Mapped[float | None] = mapped_column(Float, nullable=True)

    warehouse = relationship('Warehouse', back_populates='orders')
    item = relationship('Item', back_populates='orders')
