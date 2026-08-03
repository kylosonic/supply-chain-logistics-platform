from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class ProviderApiKey(UUIDTimestampMixin, Base):
    __tablename__ = 'provider_api_keys'

    organization_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by_user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key_name: Mapped[str] = mapped_column(String(96), nullable=False)
    masked_key: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default='active', nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
