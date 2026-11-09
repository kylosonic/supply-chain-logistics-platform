from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import UUIDString

class UserRole(StrEnum):
    ADMIN = 'admin'
    OPERATOR = 'operator'
    VIEWER = 'viewer'


class SubscriptionTier(StrEnum):
    FREE = 'free'
    STARTER = 'starter'
    SCALE = 'scale'
    ENTERPRISE = 'enterprise'


class SubscriptionStatus(StrEnum):
    TRIALING = 'trialing'
    ACTIVE = 'active'
    PAST_DUE = 'past_due'
    CANCELED = 'canceled'


class OrganizationRole(StrEnum):
    OWNER = 'owner'
    ADMIN = 'admin'
    OPERATOR = 'operator'
    VIEWER = 'viewer'


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    username: str | None = None
    identifier: str | None = None
    password: str

    @model_validator(mode='after')
    def check_identifier(self) -> 'UserLogin':
        if not self.username and not self.identifier:
            raise ValueError('username or identifier is required')
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in_seconds: int


class UserRead(BaseModel):
    id: UUIDString
    username: str
    email: str | None = None
    full_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {'from_attributes': True}

class OrganizationRead(BaseModel):
    id: UUIDString
    name: str
    slug: str
    primary_email_domain: str | None
    subscription_tier: SubscriptionTier
    subscription_status: SubscriptionStatus
    preferred_ai_provider: str | None = None
    preferred_ai_key_id: str | None = None
    created_at: datetime

    model_config = {'from_attributes': True}

class CompanySignupRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=128)
    company_email: str = Field(min_length=6, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=128)
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER


class CompanySignupResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in_seconds: int
    user: UserRead
    organization: OrganizationRead
