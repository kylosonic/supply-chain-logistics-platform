from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Inventory(UUIDTimestampMixin, Base):
    __tablename__ = 'inventory'
    __table_args__ = (UniqueConstraint('warehouse_id', 'item_id', name='uq_inventory_warehouse_item'),)

    warehouse_id: Mapped[str] = mapped_column(ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    warehouse = relationship('Warehouse', back_populates='inventory_items')
    item = relationship('Item', back_populates='inventory_records')
