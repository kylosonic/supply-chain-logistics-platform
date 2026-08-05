"""Upgrade pitch threshold crossings (blueprint decision #6).

Fire-once-per-threshold-per-month rows: ``UNIQUE(organization_id,
period_start, threshold_level)`` with levels limited to ``p60``/``p80``.
p100 is NOT stored — it is the free-cap lock state itself.

Import map: db.base, db.custom_types, models.common, sqlalchemy only.
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class ThresholdCrossing(UUIDTimestampMixin, Base):
    __tablename__ = 'threshold_crossings'
    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'period_start',
            'threshold_level',
            name='uq_threshold_crossing_org_period_level',
        ),
        CheckConstraint("threshold_level IN ('p60', 'p80')", name='ck_threshold_crossing_level'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    threshold_level: Mapped[str] = mapped_column(String(8), nullable=False)
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
