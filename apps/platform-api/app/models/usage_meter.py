from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class OrganizationUsageCounter(UUIDTimestampMixin, Base):
    __tablename__ = 'organization_usage_counters'

    organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    metric: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    used_units: Mapped[int] = mapped_column(Integer(), default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'metric', 'period_start', name='uq_usage_org_metric_period_start'),
    )
