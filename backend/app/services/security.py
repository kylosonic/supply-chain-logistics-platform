from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
from base64 import urlsafe_b64encode

import jwt

from app.core.config import settings
from app.schemas.auth import UserRole


def _pbkdf2_hash(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 120_000)
    return urlsafe_b64encode(digest).decode('utf-8')


def hash_password(password: str) -> str:
    salt = settings.password_salt
    return f'pbkdf2_sha256${salt}${_pbkdf2_hash(password, salt)}'


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, salt, hashed = hashed_password.split('$', 2)
        if algorithm != 'pbkdf2_sha256':
            return False
        candidate = _pbkdf2_hash(password, salt)
        return hmac.compare_digest(candidate, hashed)
    except Exception:
        return False


def create_access_token(subject: str, role: UserRole, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    payload = {
        'sub': subject,
        'role': role,
        'iat': int(now.timestamp()),
        'exp': int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise ValueError('Invalid or expired token') from exc
