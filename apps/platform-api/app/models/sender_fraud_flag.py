from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class SenderFraudFlag(UUIDTimestampMixin, Base):
    """Persistent per-org fraud-risk marker (TECH-21 / NB-21, decision #6).

    Keyed ``(organization_id, normalized sender_name)`` UNIQUE; rows are
    never auto-deleted, so the badge survives trusted-payer list removal
    and persists indefinitely (NB-21.3). Display-only — this table never
    gates verification (NB-21.4 / NB-21.6).
    """

    __tablename__ = 'sender_fraud_flags'
    __table_args__ = (
        UniqueConstraint('organization_id', 'sender_name', name='uq_sender_fraud_flag_org_sender'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    sender_name: Mapped[str] = mapped_column(String(128), nullable=False)
    fraud_risk_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reversal_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
