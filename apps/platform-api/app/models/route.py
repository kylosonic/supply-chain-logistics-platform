from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class RouteSchedule(UUIDTimestampMixin, Base):
    __tablename__ = 'route_schedules'

    route_name: Mapped[str] = mapped_column(String(128), nullable=False)
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_warehouse_id: Mapped[str] = mapped_column(ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False)
    assigned_asset_id: Mapped[str | None] = mapped_column(ForeignKey('fleet_assets.id', ondelete='SET NULL'), nullable=True)
    origin_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    vehicle_capacity_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    objective: Mapped[str] = mapped_column(String(32), default='weighted_cost', nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_duration_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default='planned', nullable=False)

    stops = relationship('RouteStop', back_populates='route_schedule', cascade='all, delete-orphan')
    assigned_asset = relationship('FleetAsset', foreign_keys=[assigned_asset_id])


class RouteStop(UUIDTimestampMixin, Base):
    __tablename__ = 'route_stops'

    route_schedule_id: Mapped[str] = mapped_column(ForeignKey('route_schedules.id', ondelete='CASCADE'), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    warehouse_id: Mapped[str] = mapped_column(ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False)
    planned_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    load_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    route_schedule = relationship('RouteSchedule', back_populates='stops')
