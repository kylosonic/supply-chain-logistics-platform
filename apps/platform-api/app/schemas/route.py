from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class DeliveryDemand(BaseModel):
    warehouse_code: str
    demand_units: int = Field(gt=0)


class RouteWeights(BaseModel):
    distance: float = Field(default=0.5, ge=0)
    time: float = Field(default=0.3, ge=0)
    cost: float = Field(default=0.2, ge=0)


class RouteOptimizeRequest(BaseModel):
    route_name: str = 'Auto-Optimized Route'
    schedule_date: date
    start_warehouse_code: str
    deliveries: list[DeliveryDemand]
    vehicle_capacity_units: int = Field(gt=0)
    max_stops: int = Field(default=20, ge=1)
    speed_kmh: float = Field(default=45.0, gt=0)
    cost_per_km: float = Field(default=1.5, gt=0)
    weights: RouteWeights = RouteWeights()
    persist_schedule: bool = True
    minimize_carbon_footprint: bool = False


class RouteStopOut(BaseModel):
    sequence: int
    warehouse_code: str
    demand_units: int
    leg_distance_km: float
    cumulative_distance_km: float
    latitude: float | None = None
    longitude: float | None = None
    estimated_arrival: datetime | None = None


class RouteOptimizeResponse(BaseModel):
    route_name: str
    schedule_date: date
    objective: str
    total_distance_km: float
    total_cost: float
    estimated_duration_min: int
    capacity_used: int
    unassigned_deliveries: list[DeliveryDemand]
    stops: list[RouteStopOut]
    co2_saved_kg: float | None = None
    post_aha_toast: bool = False
    data_origin: str | None = None


class RouteScheduleSummary(BaseModel):
    id: str
    route_name: str
    schedule_date: date
    total_distance_km: float
    total_cost: float
    estimated_duration_min: int
    status: str


class RouteScheduleDetail(RouteScheduleSummary):
    stops: list[RouteStopOut]


class RouteOptimizationRunSummary(ORMBase):
    route_name: str
    schedule_date: date
    start_warehouse_code: str
    objective: str
    total_distance_km: float
    total_cost: float
    estimated_duration_min: int
    capacity_used: int
    deliveries_count: int
    stops_count: int
    unassigned_count: int
    persist_requested: bool
    persisted_schedule_id: str | None
    minimize_carbon_footprint: bool
    co2_saved_kg: float | None


class RouteOptimizationRunDetail(RouteOptimizationRunSummary):
    actor_user_id: str | None
    organization_id: str | None
    vehicle_capacity_units: int
    max_stops: int
    speed_kmh: float
    cost_per_km: float
    weights: RouteWeights
    deliveries: list[DeliveryDemand]
    stops: list[RouteStopOut]
    unassigned_deliveries: list[DeliveryDemand]
