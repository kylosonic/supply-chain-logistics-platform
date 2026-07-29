from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

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


class ExceptionFeedSummary(BaseModel):
    open_alerts: int
    delayed_shipments: int
    pending_replenishment_plans: int
    route_runs_with_unassigned_deliveries: int


class ExceptionFeedResponse(BaseModel):
    summary: ExceptionFeedSummary
    items: list[ExceptionFeedItem]