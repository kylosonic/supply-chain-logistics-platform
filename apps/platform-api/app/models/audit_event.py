from typing import Any

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class AuditEvent(UUIDTimestampMixin, Base):
    __tablename__ = 'audit_events'

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON, nullable=True)