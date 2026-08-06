from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class DisputeThread(UUIDTimestampMixin, Base):
    """Rejection -> escalation conversion (TECH-17 / NB-17).

    One thread per receipt (UNIQUE receipt_id): repeat dispute cycles are
    a non-goal (blueprint decision #14).
    """

    __tablename__ = 'dispute_threads'
    __table_args__ = (
        CheckConstraint("status IN ('open','resolved')", name='ck_dispute_thread_status'),
        CheckConstraint(
            "resolution IN ('verify','maintain_rejection') OR resolution IS NULL",
            name='ck_dispute_thread_resolution',
        ),
        UniqueConstraint('receipt_id', name='uq_dispute_thread_receipt'),
    )

    receipt_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('payment_receipts.id', ondelete='CASCADE'), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    dispute_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    submitted_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default='open', nullable=False)
    resolution: Mapped[str | None] = mapped_column(String(24), nullable=True)
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
