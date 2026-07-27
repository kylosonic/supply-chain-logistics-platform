from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class User(UUIDTimestampMixin, Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(24), default='viewer', nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
