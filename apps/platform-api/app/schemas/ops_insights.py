from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.schemas.common import ORMBase


class AuditEventRead(ORMBase):
    event_type: str
    entity_type: str
    entity_id: str | None
    actor_user_id: str | None
    organization_id: str | None
    description: str
    payload: dict[str, Any] | list[Any] | None


class ExceptionFeedItem(BaseModel):
    source_type: str
    source_id: str
    severity: str
    status: str
    title: str
    message: str
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime
    metadata: dict[str, Any] | None = None

    @field_validator('source_id', 'entity_id', mode='before')
    @classmethod
    def _coerce_ids(cls, v):
        if v is None:
            return v
        return str(v) if isinstance(v, UUID) else v


class ExceptionFeedSummary(BaseModel):
    open_alerts: int
    delayed_shipments: int
    pending_replenishment_plans: int
    route_runs_with_unassigned_deliveries: int


class ExceptionFeedResponse(BaseModel):
    summary: ExceptionFeedSummary
    items: list[ExceptionFeedItem]