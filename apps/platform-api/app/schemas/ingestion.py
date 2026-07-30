from datetime import datetime

from pydantic import BaseModel, Field


class IngestionResult(BaseModel):
    records_processed: int
    records_created: int
    records_updated: int
    errors: list[str]


class TelematicsPayload(BaseModel):
    asset_id: str = Field(min_length=1, description="Vehicle code identifying the fleet asset")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_mph: float = Field(ge=0)
    heading_degrees: int = Field(ge=0, lt=360)
    timestamp: datetime


class TelematicsResult(BaseModel):
    asset_id: str
    status: str
    updated_latitude: float
    updated_longitude: float
    telemetry_timestamp: datetime
