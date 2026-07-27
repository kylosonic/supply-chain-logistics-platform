from datetime import datetime

from pydantic import BaseModel, Field


class InventoryUpsert(BaseModel):
    warehouse_code: str
    sku: str
    quantity_on_hand: int = Field(ge=0)
    safety_stock: int = Field(default=0, ge=0)


class InventoryRead(BaseModel):
    id: str
    warehouse_id: str
    item_id: str
    quantity_on_hand: int
    safety_stock: int
    updated_at: datetime | None = None

    model_config = {'from_attributes': True}


class InventoryOverviewRow(BaseModel):
    warehouse_code: str
    warehouse_name: str
    total_quantity_on_hand: int
    total_safety_stock: int
    utilization_percent: float
