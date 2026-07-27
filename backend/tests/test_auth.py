from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import settings
from app.schemas.auth import UserRole
from app.services.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify_round_trip():
    raw = 'StrongPassword!123'
    hashed = hash_password(raw)

    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password('wrong-password', hashed) is False


def test_create_and_decode_access_token_includes_sub_and_role():
    token = create_access_token(subject='user-123', role=UserRole.ADMIN)
    payload = decode_access_token(token)

    assert payload['sub'] == 'user-123'
    assert payload['role'] == UserRole.ADMIN
    assert 'exp' in payload


def test_decode_access_token_rejects_expired_token():
    expired = create_access_token(
        subject='user-123',
        role=UserRole.OPERATOR,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError):
        decode_access_token(expired)
