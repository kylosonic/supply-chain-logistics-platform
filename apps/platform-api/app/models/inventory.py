from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class Inventory(UUIDTimestampMixin, Base):
    __tablename__ = 'inventory'
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'item_id', name='uq_inventory_warehouse_item'),
        CheckConstraint("data_origin IN ('sample', 'real')", name='ck_inventory_data_origin'),
    )

    warehouse_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    data_origin: Mapped[str] = mapped_column(
        String(8), default='real', server_default='real', nullable=False
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    warehouse = relationship('Warehouse', back_populates='inventory_items')
    item = relationship('Item', back_populates='inventory_records')
