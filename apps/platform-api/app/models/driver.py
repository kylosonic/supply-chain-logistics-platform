from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class Driver(UUIDTimestampMixin, Base):
    """A person who actually drives the route (NB-86).

    Before this existed, work was assigned to a warehouse and a schedule but
    never to a human, so "who is carrying this load" lived in a phone call.
    Phone is the tenant-unique natural key: it is how an operator identifies a
    driver in practice, and it is what a future driver-facing surface would
    authenticate against.
    """

    __tablename__ = 'drivers'
    __table_args__ = (
        UniqueConstraint('organization_id', 'phone', name='uq_drivers_org_phone'),
        CheckConstraint("status IN ('active','inactive')", name='ck_drivers_status'),
        Index('ix_drivers_org_status', 'organization_id', 'status'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    license_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default='active', nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
