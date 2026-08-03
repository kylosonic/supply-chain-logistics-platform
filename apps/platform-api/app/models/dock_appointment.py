from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class DockAppointment(UUIDTimestampMixin, Base):
    __tablename__ = 'dock_appointments'

    warehouse_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('warehouses.id', ondelete='CASCADE'), index=True, nullable=False)
    truck_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default='scheduled', nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    warehouse = relationship('Warehouse')
