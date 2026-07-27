from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ItemBase(BaseModel):
    sku: str = Field(min_length=2, max_length=64)
    name: str
    category: str
    unit_cost: float = Field(default=0.0, ge=0)
    reorder_level: int = Field(default=0, ge=0)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    unit_cost: float | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)


class ItemRead(ORMBase, ItemBase):
    pass
