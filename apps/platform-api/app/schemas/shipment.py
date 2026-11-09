from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ShipmentStatus(StrEnum):
    PLANNED = 'planned'
    IN_TRANSIT = 'in_transit'
    DELIVERED = 'delivered'
    DELAYED = 'delayed'
    CANCELLED = 'cancelled'


class DriverStatus(StrEnum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class CashCollectionStatus(StrEnum):
    OUTSTANDING = 'outstanding'
    COLLECTED = 'collected'
    SETTLED = 'settled'
    VOIDED = 'voided'


class ShipmentCreate(BaseModel):
    shipment_no: str = Field(min_length=3, max_length=64)
    origin_warehouse_code: str = Field(min_length=2, max_length=32)
    destination_warehouse_code: str = Field(min_length=2, max_length=32)
    sku: str = Field(min_length=2, max_length=64)
    quantity_units: int = Field(gt=0)
    route_schedule_id: str | None = None
    planned_departure: datetime | None = None
    expected_delivery: datetime | None = None
    scope_3_emissions_kg: float = 0.0
    # NB-86
    driver_id: str | None = None
    cod_amount_etb: Decimal = Field(default=Decimal('0'), ge=0, max_digits=14, decimal_places=2)
    client_ref: str | None = Field(default=None, max_length=80)


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
    last_known_location: str | None = Field(default=None, max_length=128)
    delay_reason: str | None = Field(default=None, max_length=255)
    proof_of_delivery_ref: str | None = Field(default=None, max_length=255)
    actual_delivery: datetime | None = None
    # cash declared by the driver at the point of delivery. Supplying this
    # with a DELIVERED status opens or updates the shipment's cash record, so a
    # field confirmation and its cash figure travel in one call over one
    # connection attempt.
    cash_collected_etb: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    cash_note: str | None = Field(default=None, max_length=500)


class ShipmentAssignDriver(BaseModel):
    driver_id: str | None = None


class ShipmentRead(ORMBase):
    shipment_no: str
    route_schedule_id: str | None
    origin_warehouse_code: str
    destination_warehouse_code: str
    sku: str
    quantity_units: int
    planned_departure: datetime | None
    expected_delivery: datetime | None
    actual_delivery: datetime | None
    status: ShipmentStatus
    last_known_location: str | None
    delay_reason: str | None
    proof_of_delivery_ref: str | None
    scope_3_emissions_kg: float
    # NB-86
    driver_id: str | None = None
    driver_name: str | None = None
    cod_amount_etb: Decimal = Decimal('0')
    client_ref: str | None = None


class DriverCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=5, max_length=32)
    license_no: str | None = Field(default=None, max_length=64)
    vehicle_plate: str | None = Field(default=None, max_length=32)
    status: DriverStatus = DriverStatus.ACTIVE
    notes: str | None = Field(default=None, max_length=500)


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    license_no: str | None = Field(default=None, max_length=64)
    vehicle_plate: str | None = Field(default=None, max_length=32)
    status: DriverStatus | None = None
    notes: str | None = Field(default=None, max_length=500)


class DriverRead(ORMBase):
    full_name: str
    phone: str
    license_no: str | None
    vehicle_plate: str | None
    status: DriverStatus
    notes: str | None


class DriverShipmentRead(ORMBase):
    """A row in "what is this driver carrying" — deliberately narrow."""

    shipment_no: str
    status: ShipmentStatus
    expected_delivery: datetime | None
    cod_amount_etb: Decimal


class CashCollectionRead(ORMBase):
    shipment_id: str
    shipment_no: str
    driver_id: str | None
    driver_name: str | None
    expected_etb: Decimal
    collected_etb: Decimal
    shortfall_etb: Decimal
    status: CashCollectionStatus
    collected_at: datetime | None
    settled_at: datetime | None
    note: str | None


class CashCollectionDeclare(BaseModel):
    """A driver (or an operator on their behalf) declares what they hold."""

    collected_etb: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    note: str | None = Field(default=None, max_length=500)


class CashCollectionSettle(BaseModel):
    """The office receives the cash and closes the record."""

    note: str | None = Field(default=None, max_length=500)


class CashLedgerSummary(BaseModel):
    """The end-of-day question: how much cash is out, and how much is missing."""

    outstanding_count: int
    outstanding_expected_etb: Decimal
    collected_count: int
    collected_etb: Decimal
    settled_count: int
    settled_etb: Decimal
    shortfall_etb: Decimal
