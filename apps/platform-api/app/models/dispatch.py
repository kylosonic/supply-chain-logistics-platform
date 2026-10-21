from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class Customer(UUIDTimestampMixin, Base):
    __tablename__ = 'customers'
    __table_args__ = (UniqueConstraint('organization_id', 'code', name='uq_customers_org_code'),)

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DispatchRun(UUIDTimestampMixin, Base):
    __tablename__ = 'dispatch_runs'

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    route_name: Mapped[str] = mapped_column(String(128), nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_label: Mapped[str] = mapped_column(String(160), nullable=False)
    start_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    start_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_capacity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    max_stops: Mapped[int] = mapped_column(Integer, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_duration_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_cash_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal('0'), nullable=False)
    stops_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    unassigned_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default='planned', nullable=False)
    driver_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True, index=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    cash_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeliveryOrder(UUIDTimestampMixin, Base):
    __tablename__ = 'delivery_orders'
    __table_args__ = (
        UniqueConstraint('organization_id', 'order_no', name='uq_delivery_orders_org_order_no'),
        Index('ix_delivery_orders_dispatch_sequence', 'dispatch_run_id', 'stop_sequence'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('customers.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    item_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('items.id', ondelete='SET NULL'), nullable=True
    )
    dispatch_run_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('dispatch_runs.id', ondelete='SET NULL'), nullable=True, index=True
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        UUIDType, ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True, index=True
    )
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    cod_amount_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal('0'), nullable=False)
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    stop_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default='planned', nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_cash_etb: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal('0'), nullable=False)
    cash_declared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cash_settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cash_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeliveryProof(UUIDTimestampMixin, Base):
    __tablename__ = 'delivery_proofs'
    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'delivery_order_id',
            'proof_sequence',
            name='uq_delivery_proofs_order_sequence',
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    delivery_order_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('delivery_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    proof_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    proof_kind: Mapped[str] = mapped_column(String(16), default='photo', nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
