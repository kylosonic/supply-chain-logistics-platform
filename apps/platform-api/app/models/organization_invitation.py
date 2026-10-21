from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class OrganizationInvitation(UUIDTimestampMixin, Base):
    __tablename__ = 'organization_invitations'
    __table_args__ = (
        Index(
            'ix_org_invitations_org_status',
            'organization_id',
            'status',
        ),
        Index(
            'ix_org_invitations_email_status',
            'email',
            'status',
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(24), default='viewer', nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    invited_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(16), default='pending', nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
