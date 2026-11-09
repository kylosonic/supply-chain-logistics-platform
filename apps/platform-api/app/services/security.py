from __future__ import annotations

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.fernet import Fernet

from app.core.config import settings
from app.schemas.auth import UserRole

_PBKDF2_ITERATIONS = 600_000


def _pbkdf2_hash(password: str, salt: str, iterations: int = _PBKDF2_ITERATIONS) -> str:
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return urlsafe_b64encode(digest).decode('utf-8')


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
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


def create_access_token(
    subject: str,
    role: UserRole,
    expires_delta: timedelta | None = None,
    token_version: int = 0,
) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    payload = {
        'sub': str(subject),
        'role': role,
        'ver': token_version,
        'iat': int(now.timestamp()),
        'exp': int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.effective_jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token_for_org(
    subject: str,
    role: UserRole,
    organization_id: str,
    expires_delta: timedelta | None = None,
    token_version: int = 0,
) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    payload = {
        'sub': str(subject),
        'role': role,
        'org_id': str(organization_id),
        'ver': token_version,
        'iat': int(now.timestamp()),
        'exp': int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.effective_jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.effective_jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise ValueError('Invalid or expired token') from exc


def _provider_key_fernet() -> Fernet:
    # seeded from the guarded effective secret; dev/test fallback
    # to the JWT secret is preserved when the raw value is empty.
    seed = settings.effective_provider_key_encryption_secret or settings.effective_jwt_secret_key
    digest = hashlib.sha256(seed.encode('utf-8')).digest()
    key = urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_provider_key(raw_key: str) -> str:
    token = _provider_key_fernet().encrypt(raw_key.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_provider_key(encrypted_key: str) -> str:
    raw = _provider_key_fernet().decrypt(encrypted_key.encode('utf-8'))
    return raw.decode('utf-8')


def mask_provider_key(raw_key: str) -> str:
    cleaned = raw_key.strip()
    if len(cleaned) <= 8:
        return '*' * len(cleaned)
    return f'{cleaned[:4]}***{cleaned[-4:]}'
