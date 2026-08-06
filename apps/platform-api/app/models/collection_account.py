from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class CollectionAccount(UUIDTimestampMixin, Base):
    """System collection account (CBE or Dashen) designated on invoices.

    NB-02: exactly two accounts exist in a single configuration surface.
    ``bank_code`` is constrained to the in-portfolio banks.
    """

    __tablename__ = 'collection_accounts'
    __table_args__ = (
        CheckConstraint("bank_code IN ('cbe', 'dashen')", name='ck_collection_account_bank_code'),
    )

    bank_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    bank_name: Mapped[str] = mapped_column(String(64), nullable=False)
    account_holder: Mapped[str] = mapped_column(String(128), nullable=False)
    account_number: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
