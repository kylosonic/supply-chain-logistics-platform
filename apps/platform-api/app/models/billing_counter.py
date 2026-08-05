from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BillingCounter(Base):
    """Single-row sequence counter for invoice numbers.

    Invoice numbers render as ``INV-{last_value:06d}``. The row is fixed at
    id=1 and seeded by the Phase 1 migration.
    """

    __tablename__ = 'billing_counters'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
