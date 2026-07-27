from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Warehouse(UUIDTimestampMixin, Base):
    __tablename__ = 'warehouses'

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    inventory_items = relationship('Inventory', back_populates='warehouse', cascade='all, delete-orphan')
    orders = relationship('HistoricalOrder', back_populates='warehouse')
