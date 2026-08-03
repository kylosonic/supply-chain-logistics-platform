from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.custom_types import UUIDType


class UUIDTimestampMixin:
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
