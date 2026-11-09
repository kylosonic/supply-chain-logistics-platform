from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import UUIDString


class ProviderKeyCreateRequest(BaseModel):
    provider_name: str = Field(min_length=2, max_length=64)
    key_name: str = Field(min_length=2, max_length=96)
    api_key: str = Field(min_length=8, max_length=2048)


class ProviderKeyRead(BaseModel):
    id: UUIDString
    provider_name: str
    key_name: str
    masked_key: str
    status: str
    created_at: datetime
    revoked_at: datetime | None

    model_config = {'from_attributes': True}

class ProviderKeyRevokeRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class ProviderKeyTestResponse(BaseModel):
    key_id: UUIDString
    provider_name: str
    ok: bool
    message: str

class ProviderPreferenceRequest(BaseModel):
    key_id: UUIDString


class ProviderPreferenceRead(BaseModel):
    organization_id: UUIDString
    provider_name: str | None
    key_id: UUIDString | None

    model_config = {'from_attributes': True}
