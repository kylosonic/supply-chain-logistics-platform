from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class FleetAsset(UUIDTimestampMixin, Base):
    __tablename__ = 'fleet_assets'
    __table_args__ = (
        UniqueConstraint('organization_id', 'vehicle_code', name='uq_fleet_assets_org_vehicle_code'),
        CheckConstraint("data_origin IN ('sample', 'real')", name='ck_fleet_assets_data_origin'),
    )

    vehicle_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    driver_name: Mapped[str] = mapped_column(String(128), nullable=False)
    driver_contact: Mapped[str | None] = mapped_column(String(128), nullable=True)
    capacity_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default='active', nullable=False)
    data_origin: Mapped[str] = mapped_column(
        String(8), default='real', server_default='real', nullable=False
    )
    organization_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_telemetry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
