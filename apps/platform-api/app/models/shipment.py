from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin
from uuid import UUID
from app.db.custom_types import UUIDType


class Shipment(UUIDTimestampMixin, Base):
    __tablename__ = 'shipments'

    # TECH-49 / NB-64: a shipment number is unique *within its tenant*, not
    # globally. Two partial unique indexes are used instead of one composite
    # index because SQL treats NULLs as distinct, which would leave
    # unattributed legacy rows unconstrained; mirror of migration
    # 20260811_0019 ``_repair_shipment_number_uniqueness``.
    __table_args__ = (
        Index(
            'uq_shipments_org_shipment_no',
            'organization_id',
            'shipment_no',
            unique=True,
            sqlite_where=text('organization_id IS NOT NULL'),
            postgresql_where=text('organization_id IS NOT NULL'),
        ),
        Index(
            'uq_shipments_unattributed_shipment_no',
            'shipment_no',
            unique=True,
            sqlite_where=text('organization_id IS NULL'),
            postgresql_where=text('organization_id IS NULL'),
        ),
        Index('ix_shipments_shipment_no_lookup', 'shipment_no'),
    )

    # NB-64 (audit H-1): tenant scoping. Nullable for legacy rows created
    # before org scoping; backfilled in migration 20260811_0019.
    organization_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True
    )
    shipment_no: Mapped[str] = mapped_column(String(64), nullable=False)
    route_schedule_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey('route_schedules.id', ondelete='SET NULL'), nullable=True)
    origin_warehouse_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True)
    destination_warehouse_id: Mapped[str] = mapped_column(
        ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True
    )
    item_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey('items.id', ondelete='RESTRICT'), nullable=False, index=True)
    quantity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default='planned', nullable=False, index=True)
    last_known_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    delay_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_of_delivery_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope_3_emissions_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
