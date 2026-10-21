from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class CustomerCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    address: str = Field(min_length=2, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    notes: str | None = Field(default=None, max_length=500)


class CustomerRead(ORMBase):
    code: str
    name: str
    phone: str | None
    address: str
    latitude: float
    longitude: float
    notes: str | None


class DeliveryOrderCreate(BaseModel):
    order_no: str = Field(min_length=2, max_length=64)
    customer_id: str
    item_id: str | None = None
    quantity_units: int = Field(gt=0, le=100000)
    cod_amount_etb: Decimal = Field(default=Decimal('0'), ge=0, max_digits=14, decimal_places=2)
    window_start: datetime | None = None
    window_end: datetime | None = None
    service_minutes: int = Field(default=15, ge=0, le=240)
    priority: int = Field(default=3, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=500)


class DeliveryOrderRead(ORMBase):
    id: str
    order_no: str
    customer_id: str
    customer_code: str | None = None
    customer_name: str | None = None
    item_id: str | None
    dispatch_run_id: str | None
    driver_id: str | None
    quantity_units: int
    cod_amount_etb: Decimal
    window_start: datetime | None
    window_end: datetime | None
    service_minutes: int
    priority: int
    stop_sequence: int | None
    status: str
    completed_at: datetime | None
    collected_cash_etb: Decimal
    cash_declared_at: datetime | None
    cash_settled_at: datetime | None
    cash_note: str | None
    notes: str | None


class DispatchPlanRequest(BaseModel):
    route_name: str = Field(min_length=2, max_length=128)
    plan_date: date
    start_label: str = Field(min_length=2, max_length=160)
    start_latitude: float = Field(ge=-90, le=90)
    start_longitude: float = Field(ge=-180, le=180)
    order_ids: list[str] = Field(min_length=1, max_length=200)
    driver_id: str | None = None
    vehicle_capacity_units: int = Field(gt=0, le=100000)
    max_stops: int = Field(default=100, ge=1, le=100)
    average_speed_kmh: float = Field(default=30, gt=0, le=120)
    start_time: datetime | None = None
    cost_per_km: Decimal = Field(default=Decimal('0'), ge=0, max_digits=14, decimal_places=2)


class DispatchStopRead(BaseModel):
    order_id: str
    order_no: str
    customer_code: str
    customer_name: str
    address: str
    phone: str | None
    latitude: float
    longitude: float
    sequence: int
    planned_arrival: datetime
    window_start: datetime | None
    window_end: datetime | None
    demand_units: int
    cod_amount_etb: Decimal
    status: str
    completed_at: datetime | None
    collected_cash_etb: Decimal
    proof_id: str | None = None


class DispatchRunRead(ORMBase):
    id: str
    route_name: str
    plan_date: date
    start_label: str
    vehicle_capacity_units: int
    max_stops: int
    total_distance_km: float
    estimated_duration_min: int
    expected_cash_etb: Decimal
    status: str
    driver_id: str | None
    cash_closed_at: datetime | None


class DispatchRunDetail(DispatchRunRead):
    stops: list[DispatchStopRead] = Field(default_factory=list)
    unassigned: list[dict] = Field(default_factory=list)


class DriverLinkResponse(BaseModel):
    token: str
    driver_url: str
    expires_at: datetime


class DriverManifest(BaseModel):
    run_id: str
    route_name: str
    plan_date: date
    driver_id: str
    driver_name: str
    start_label: str
    stops: list[DispatchStopRead]


class DriverStatusUpdate(BaseModel):
    status: str = Field(pattern='^(in_transit|delivered|failed)$')
    note: str | None = Field(default=None, max_length=500)


class DriverCashDeclare(BaseModel):
    collected_etb: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    note: str | None = Field(default=None, max_length=500)


class CashCloseSummary(BaseModel):
    run_id: str
    expected_etb: Decimal
    collected_etb: Decimal
    shortfall_etb: Decimal
    terminal_stops: int
    total_stops: int
    closed_at: datetime


class DeliveryProofRead(ORMBase):
    id: str
    delivery_order_id: str
    proof_kind: str
    content_type: str
    recipient_name: str | None
    notes: str | None
    captured_at: datetime
