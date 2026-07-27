from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    ADMIN = 'admin'
    OPERATOR = 'operator'
    VIEWER = 'viewer'


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in_seconds: int


class UserRead(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {'from_attributes': True}
