from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class RouteOptimizationRun(UUIDTimestampMixin, Base):
    __tablename__ = 'route_optimization_runs'

    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    persisted_schedule_id: Mapped[str | None] = mapped_column(ForeignKey('route_schedules.id', ondelete='SET NULL'), nullable=True, index=True)
    route_name: Mapped[str] = mapped_column(String(128), nullable=False)
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_warehouse_code: Mapped[str] = mapped_column(String(32), nullable=False)
    vehicle_capacity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    max_stops: Mapped[int] = mapped_column(Integer, nullable=False)
    speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    cost_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    objective: Mapped[str] = mapped_column(String(32), nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_used: Mapped[int] = mapped_column(Integer, nullable=False)
    deliveries_count: Mapped[int] = mapped_column(Integer, nullable=False)
    stops_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unassigned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    persist_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deliveries_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    weights_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    stops_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    unassigned_deliveries_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)