from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class AlertType(StrEnum):
    LOW_STOCK = 'low_stock'
    DELAYED_SHIPMENT = 'delayed_shipment'
    PLANNING_EXCEPTION = 'planning_exception'
    MANUAL = 'manual'


class AlertSeverity(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class AlertStatus(StrEnum):
    OPEN = 'open'
    ACKNOWLEDGED = 'acknowledged'
    RESOLVED = 'resolved'


class AlertCreate(BaseModel):
    alert_type: AlertType = AlertType.MANUAL
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = Field(min_length=3, max_length=128)
    message: str = Field(min_length=3, max_length=500)
    related_entity_type: str | None = Field(default=None, max_length=64)
    related_entity_id: str | None = Field(default=None, max_length=64)


class AlertAction(BaseModel):
    note: str | None = Field(default=None, max_length=255)


class AlertRead(ORMBase):
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    related_entity_type: str | None
    related_entity_id: str | None
    acknowledged_by_user_id: str | None
    acknowledged_at: datetime | None
    resolved_by_user_id: str | None
    resolved_at: datetime | None
    resolution_note: str | None
