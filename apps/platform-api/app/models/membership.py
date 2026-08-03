from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class OrganizationMembership(UUIDTimestampMixin, Base):
    __tablename__ = 'organization_memberships'
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_membership_org_user'),
    )

    organization_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(24), default='viewer', nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
