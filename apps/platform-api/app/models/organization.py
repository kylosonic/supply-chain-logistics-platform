from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class Organization(UUIDTimestampMixin, Base):
    __tablename__ = 'organizations'

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    primary_email_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(24), default='starter', nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(24), default='trialing', nullable=False)
    billing_phase: Mapped[str] = mapped_column(
        String(24), server_default='free', nullable=False
    )
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferred_ai_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preferred_ai_key_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(24), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
