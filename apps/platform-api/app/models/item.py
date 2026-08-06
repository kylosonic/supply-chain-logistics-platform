from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class Item(UUIDTimestampMixin, Base):
    __tablename__ = 'items'
    __table_args__ = (
        UniqueConstraint('organization_id', 'sku', name='uq_items_org_sku'),
        CheckConstraint("data_origin IN ('sample', 'real')", name='ck_items_data_origin'),
    )

    sku: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    temperature_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_origin: Mapped[str] = mapped_column(
        String(8), default='real', server_default='real', nullable=False
    )
    organization_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)

    inventory_records = relationship('Inventory', back_populates='item', cascade='all, delete-orphan')
    orders = relationship('HistoricalOrder', back_populates='item')
