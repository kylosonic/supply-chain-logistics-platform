from datetime import datetime
from pydantic import BaseModel
from app.schemas.common import ORMBase

class DockAppointmentPayload(BaseModel):
    warehouse_id: str
    truck_id: str
    expected_time: datetime

class DockAppointmentResponse(ORMBase):
    warehouse_id: str
    truck_id: str
    status: str
    scheduled_time: datetime
    expected_time: datetime
