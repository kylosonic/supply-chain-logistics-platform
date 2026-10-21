from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class DeliveryDemand(BaseModel):
    warehouse_code: str = Field(min_length=1, max_length=32)
    demand_units: int = Field(gt=0)


class RouteWeights(BaseModel):
    distance: float = Field(default=0.5, ge=0)
    time: float = Field(default=0.3, ge=0)
    cost: float = Field(default=0.2, ge=0)


class RouteOptimizeRequest(BaseModel):
    route_name: str = Field(default='Auto-Optimized Route', min_length=1, max_length=128)
    schedule_date: date
    start_warehouse_code: str = Field(min_length=1, max_length=32)
    deliveries: list[DeliveryDemand] = Field(min_length=1, max_length=200)
    vehicle_capacity_units: int = Field(gt=0)
    max_stops: int = Field(default=20, ge=1, le=100)
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


class RouteFactorShare(BaseModel):
    distance: float
    time: float
    cost: float


class RouteDecisionPoint(BaseModel):
    sequence: int
    chosen_warehouse_code: str
    chosen_weighted_cost: float
    runner_up_warehouse_code: str | None = None
    runner_up_weighted_cost: float | None = None
    margin: float | None = None
    dominant_factor: str
    capacity_excluded_count: int = 0
    reason: str


class RouteAlternativeSummary(BaseModel):
    first_stop_warehouse_code: str
    total_distance_km: float
    estimated_duration_min: int
    total_cost: float
    distance_delta_km: float
    duration_delta_min: int
    cost_delta: float
    summary: str


class RouteDecisionExplanation(BaseModel):
    method: str
    summary: str
    dominant_factor: str
    factor_share_pct: RouteFactorShare
    constraints: list[str] = []
    decision_points: list[RouteDecisionPoint] = []
    runner_up: RouteAlternativeSummary | None = None
    limitations: list[str] = []


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
    decision_explanation: RouteDecisionExplanation | None = None


class RouteScheduleSummary(ORMBase):
    """NB-64 fix: this summary previously extended plain ``BaseModel`` while
    declaring ``id: str``, so serialising a real ``RouteSchedule`` row (whose
    ``id`` is a ``UUID``) raised ``ResponseValidationError`` -> HTTP 500 on
    ``GET /routes/schedules``. It was invisible only because no test listed a
    schedule that a request had persisted. ``ORMBase`` coerces UUIDs to strings
    (same contract as ``RouteOptimizationRunSummary``)."""

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
    decision_explanation: RouteDecisionExplanation | None = None
