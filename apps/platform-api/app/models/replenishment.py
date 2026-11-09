from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class ReplenishmentPlan(UUIDTimestampMixin, Base):
    __tablename__ = 'replenishment_plans'

    # tenant scoping. Nullable for legacy rows created
    # before org scoping; backfilled in migration 20260811_0019.
    organization_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    horizon_weeks: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    avg_weekly_demand: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    suggested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default='pending_approval', nullable=False, index=True)
    rationale: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
