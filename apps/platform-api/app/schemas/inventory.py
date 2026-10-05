from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class InventoryUpsert(BaseModel):
    warehouse_code: str
    sku: str
    quantity_on_hand: int = Field(ge=0)
    safety_stock: int = Field(default=0, ge=0)


class InventoryRead(BaseModel):
    """One inventory row.

    ``id``, ``warehouse_id`` and ``item_id`` are UUIDs on the model
    (``UUIDTimestampMixin``, and the two FKs), while this schema declares them as
    strings. Pydantic does not coerce ``UUID`` to ``str``, so serialising a real
    row raised ``ResponseValidationError`` -> **HTTP 500 on ``GET
    /api/v1/inventory`` for every tenant**, which no test caught because the
    endpoint had no test and the console reads ``/inventory/overview`` instead
    (that projection carries no ids, which is why it was unaffected).

    This is the same defect class recorded against ``RouteScheduleSummary`` in
    ``app/schemas/route.py`` (NB-64). The fix is the same idea, applied at the
    field level so the response shape is unchanged: coerce the UUIDs to strings
    on the way in.
    """

    id: str
    warehouse_id: str
    item_id: str
    quantity_on_hand: int
    safety_stock: int
    updated_at: datetime | None = None

    model_config = {'from_attributes': True}

    @field_validator('id', 'warehouse_id', 'item_id', mode='before')
    @classmethod
    def _coerce_uuid_to_str(cls, value):
        return str(value) if isinstance(value, UUID) else value


class InventoryOverviewRow(BaseModel):
    warehouse_code: str
    warehouse_name: str
    total_quantity_on_hand: int
    total_safety_stock: int
    utilization_percent: float
