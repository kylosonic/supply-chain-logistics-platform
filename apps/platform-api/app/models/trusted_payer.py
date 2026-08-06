from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class TrustedPayer(UUIDTimestampMixin, Base):
    """Per-org admin-only trusted-payer list (TECH-11 / NB-11).

    ``sender_name`` is stored normalized (casefold + strip + collapsed
    whitespace); the (organization_id, sender_name) pair is unique.
    """

    __tablename__ = 'trusted_payers'
    __table_args__ = (
        UniqueConstraint('organization_id', 'sender_name', name='uq_trusted_payer_org_sender'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False
    )
    sender_name: Mapped[str] = mapped_column(String(128), nullable=False)
    added_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
