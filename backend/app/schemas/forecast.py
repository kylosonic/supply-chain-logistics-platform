from datetime import date

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    horizon_weeks: int = Field(default=4, ge=1, le=26)


class ForecastPoint(BaseModel):
    week_start: date
    warehouse_code: str
    sku: str
    predicted_demand: float


class ForecastResponse(BaseModel):
    horizon_weeks: int
    model_name: str
    points: list[ForecastPoint]
