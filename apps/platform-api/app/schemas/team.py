from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import OrganizationRead, UserRead
from app.schemas.common import ORMBase

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class InviteRole(StrEnum):
    ADMIN = 'admin'
    OPERATOR = 'operator'
    VIEWER = 'viewer'


class InvitationCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: InviteRole = InviteRole.VIEWER

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValueError('Enter a valid email address')
        return normalized


class InvitationRead(ORMBase):
    email: str
    role: InviteRole
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime


class InvitationCreated(BaseModel):
    invitation: InvitationRead
    token: str
    invite_url: str


class InvitationAccept(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=128)


class InvitationAcceptResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in_seconds: int
    user: UserRead
    organization: OrganizationRead
    organization_role: str


class OrganizationMemberRead(BaseModel):
    membership_id: str
    user_id: str
    username: str
    email: str | None = None
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime


class MemberRoleUpdate(BaseModel):
    role: InviteRole
