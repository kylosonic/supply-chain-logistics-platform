from datetime import datetime

from pydantic import BaseModel


class ORMBase(BaseModel):
    id: str
    created_at: datetime

    model_config = {'from_attributes': True}
