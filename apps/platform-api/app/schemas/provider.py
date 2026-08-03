from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProviderKeyCreateRequest(BaseModel):
    provider_name: str = Field(min_length=2, max_length=64)
    key_name: str = Field(min_length=2, max_length=96)
    api_key: str = Field(min_length=8, max_length=2048)


class ProviderKeyRead(BaseModel):
    id: str
    provider_name: str
    key_name: str
    masked_key: str
    status: str
    created_at: datetime
    revoked_at: datetime | None

    model_config = {'from_attributes': True}

    @field_validator('id', mode='before')
    @classmethod
    def _coerce_id(cls, v):
        return str(v) if isinstance(v, UUID) else v


class ProviderKeyRevokeRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class ProviderKeyTestResponse(BaseModel):
    key_id: str
    provider_name: str
    ok: bool
    message: str

    @field_validator('key_id', mode='before')
    @classmethod
    def _coerce_key_id(cls, v):
        return str(v) if isinstance(v, UUID) else v


class ProviderPreferenceRequest(BaseModel):
    key_id: str


class ProviderPreferenceRead(BaseModel):
    organization_id: str
    provider_name: str | None
    key_id: str | None

    model_config = {'from_attributes': True}

    @field_validator('organization_id', 'key_id', mode='before')
    @classmethod
    def _coerce_ids(cls, v):
        if v is None:
            return v
        return str(v) if isinstance(v, UUID) else v
