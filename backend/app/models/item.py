from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Item(UUIDTimestampMixin, Base):
    __tablename__ = 'items'

    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    inventory_records = relationship('Inventory', back_populates='item', cascade='all, delete-orphan')
    orders = relationship('HistoricalOrder', back_populates='item')
