from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class TrialRecord(UUIDTimestampMixin, Base):
    """One paid-tier trial per (organization, tier) — trials never stack."""

    __tablename__ = 'trial_records'
    __table_args__ = (
        UniqueConstraint('organization_id', 'tier', name='uq_trial_record_org_tier'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    tier: Mapped[str] = mapped_column(String(24), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
