from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class SmsMessage(UUIDTimestampMixin, Base):
    """SMS outbox (TECH-16 / NB-16).

    ``enqueue_sms`` writes ``queued`` rows; a gateway attaches later by
    polling ``status='queued'``. No real gateway call exists in Phase 2.
    """

    __tablename__ = 'sms_messages'
    __table_args__ = (
        CheckConstraint("status IN ('queued','sent','failed')", name='ck_sms_message_status'),
        CheckConstraint("length(body) <= 200", name='ck_sms_message_body_length'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    receipt_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('payment_receipts.id', ondelete='SET NULL'), nullable=True
    )
    to_phone: Mapped[str] = mapped_column(String(24), nullable=False)
    body: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default='queued', nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gateway_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
