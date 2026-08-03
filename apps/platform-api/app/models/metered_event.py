from uuid import UUID

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class MeteredEvent(UUIDTimestampMixin, Base):
    __tablename__ = 'metered_events'

    organization_id: Mapped[UUID] = mapped_column(UUIDType, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    units: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
