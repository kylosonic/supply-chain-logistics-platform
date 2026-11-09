from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, model_validator


def _uuid_to_str(v: Any) -> Any:
    if isinstance(v, UUID):
        return str(v)
    return v


UUIDString = Annotated[str, BeforeValidator(_uuid_to_str)]


class ORMBase(BaseModel):
    id: UUIDString
    created_at: datetime

    model_config = {'from_attributes': True}

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
