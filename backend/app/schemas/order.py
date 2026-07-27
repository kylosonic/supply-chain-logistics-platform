from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class HistoricalOrderCreate(BaseModel):
    order_date: date
    warehouse_code: str
    sku: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(default=0.0, ge=0)
    customer_region: str = 'unknown'
    weather_avg_temp_c: float | None = None
    weather_precip_mm: float | None = None
    weather_disruption_index: float | None = Field(default=None, ge=0, le=1)


class HistoricalOrderRead(ORMBase):
    order_date: date
    warehouse_id: str
    item_id: str
    quantity: int
    unit_price: float
    customer_region: str
    weather_avg_temp_c: float | None
    weather_precip_mm: float | None
    weather_disruption_index: float | None

    model_config = {'from_attributes': True}
