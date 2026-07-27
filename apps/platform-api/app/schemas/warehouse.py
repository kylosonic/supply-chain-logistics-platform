from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class WarehouseBase(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str
    address: str
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    capacity_units: int = Field(ge=0, default=0)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity_units: int | None = Field(default=None, ge=0)


class WarehouseRead(ORMBase, WarehouseBase):
    pass
