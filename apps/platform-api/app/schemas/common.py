from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator


def _uuid_to_str(v):
    if isinstance(v, UUID):
        return str(v)
    return v


class ORMBase(BaseModel):
    id: str
    created_at: datetime

    model_config = {'from_attributes': True}

    @field_validator('id', mode='before')
    @classmethod
    def _coerce_id(cls, v):
        return _uuid_to_str(v)

    @model_validator(mode='before')
    @classmethod
    def _coerce_all_uuids(cls, data):
        if isinstance(data, dict):
            return {k: str(v) if isinstance(v, UUID) else v for k, v in data.items()}
        if data is not None and not isinstance(data, (str, int, float, bool, list)):
            result = {}
            for attr in dir(data):
                if attr.startswith('_'):
                    continue
                try:
                    val = getattr(data, attr)
                    result[attr] = str(val) if isinstance(val, UUID) else val
                except Exception:
                    continue
            return result
        return data
