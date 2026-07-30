from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Shipment(UUIDTimestampMixin, Base):
    __tablename__ = 'shipments'

    shipment_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    route_schedule_id: Mapped[str | None] = mapped_column(ForeignKey('route_schedules.id', ondelete='SET NULL'), nullable=True)
    origin_warehouse_id: Mapped[str] = mapped_column(ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True)
    destination_warehouse_id: Mapped[str] = mapped_column(
        ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(ForeignKey('items.id', ondelete='RESTRICT'), nullable=False, index=True)
    quantity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default='planned', nullable=False, index=True)
    last_known_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    delay_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_of_delivery_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope_3_emissions_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
