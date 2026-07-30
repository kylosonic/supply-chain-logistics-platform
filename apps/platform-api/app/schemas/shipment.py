from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ShipmentStatus(StrEnum):
    PLANNED = 'planned'
    IN_TRANSIT = 'in_transit'
    DELIVERED = 'delivered'
    DELAYED = 'delayed'
    CANCELLED = 'cancelled'


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


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
    last_known_location: str | None = Field(default=None, max_length=128)
    delay_reason: str | None = Field(default=None, max_length=255)
    proof_of_delivery_ref: str | None = Field(default=None, max_length=255)
    actual_delivery: datetime | None = None


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
