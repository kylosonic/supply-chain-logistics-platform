from datetime import date

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    horizon_weeks: int = Field(default=4, ge=1, le=26)


class ForecastPoint(BaseModel):
    week_start: date
    warehouse_code: str
    sku: str
    predicted_demand: float
    planning_low: float
    planning_high: float


class ForecastQuality(BaseModel):
    status: str
    history_weeks: int
    holdout_weeks: int
    evaluated_rows: int
    mae: float | None = None
    wape_percent: float | None = None
    range_basis: str
    interpretation: str
    caveat: str


class ForecastResponse(BaseModel):
    horizon_weeks: int
    model_name: str
    points: list[ForecastPoint]
    quality: ForecastQuality
