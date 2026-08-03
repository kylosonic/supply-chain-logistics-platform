from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class FleetAsset(UUIDTimestampMixin, Base):
    __tablename__ = 'fleet_assets'

    vehicle_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    driver_name: Mapped[str] = mapped_column(String(128), nullable=False)
    driver_contact: Mapped[str | None] = mapped_column(String(128), nullable=True)
    capacity_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default='active', nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_telemetry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
