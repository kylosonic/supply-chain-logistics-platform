from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class Warehouse(UUIDTimestampMixin, Base):
    __tablename__ = 'warehouses'
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uq_warehouses_org_code'),
        CheckConstraint("data_origin IN ('sample', 'real')", name='ck_warehouses_data_origin'),
    )

    code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_origin: Mapped[str] = mapped_column(
        String(8), default='real', server_default='real', nullable=False
    )
    organization_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)

    inventory_items = relationship('Inventory', back_populates='warehouse', cascade='all, delete-orphan')
    orders = relationship('HistoricalOrder', back_populates='warehouse')
