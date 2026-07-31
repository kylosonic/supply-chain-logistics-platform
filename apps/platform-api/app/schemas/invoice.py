from pydantic import BaseModel
from app.schemas.common import ORMBase

class FreightInvoiceRead(ORMBase):
    order_id: str
    carrier_id: str
    quoted_rate: float
    actual_rate: float
    variance: float
    status: str
