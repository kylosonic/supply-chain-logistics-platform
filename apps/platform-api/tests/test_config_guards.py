"""PROD-02/04/05 config guardrail tests.

Every test constructs ``Settings(_env_file=None, ...)`` with the other
required production fields set, isolating the guard under test. Guards are
lazy properties: they raise on ACCESS in non-dev environments, and dev/test
defaults skip them entirely.
"""
from __future__ import annotations

import pytest

from app.core.config import Settings


def _prod_settings(**overrides) -> Settings:
    base = {
        'app_env': 'production',
        'database_url': 'postgresql+psycopg://user:pass@db:5432/supply_chain',
        'jwt_secret_key': 'prod-jwt-secret-minimum-32-chars-long!!',
        'provider_key_encryption_secret': 'prod-provider-key-secret-minimum-32!!',
        'receipt_extraction_mode': 'real',
        'cbe_account_holder': 'FreightPilot PLC',
        'cbe_account_number': '1000134567890',
        'dashen_account_holder': 'FreightPilot PLC',
        'dashen_account_number': '012345678901',
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


# --- PROD-02: receipt-extraction mode guard --------------------------------

def test_production_extraction_mode_rejects_mock():
    s = _prod_settings(receipt_extraction_mode='mock')
    with pytest.raises(ValueError, match='RECEIPT_EXTRACTION_MODE'):
        s.effective_receipt_extraction_mode


def test_production_extraction_mode_accepts_real():
    s = _prod_settings()
    assert s.effective_receipt_extraction_mode == 'real'


# --- PROD-04: CBE/Dashen collection-account guards --------------------------

def test_production_cbe_holder_required():
    s = _prod_settings(cbe_account_holder='')
    with pytest.raises(ValueError, match='CBE_ACCOUNT_HOLDER'):
        s.effective_cbe_account_holder


def test_production_cbe_number_required():
    s = _prod_settings(cbe_account_number='')
    with pytest.raises(ValueError, match='CBE_ACCOUNT_NUMBER'):
        s.effective_cbe_account_number


def test_production_dashen_holder_required():
    s = _prod_settings(dashen_account_holder='')
    with pytest.raises(ValueError, match='DASHEN_ACCOUNT_HOLDER'):
        s.effective_dashen_account_holder


def test_production_dashen_number_required():
    s = _prod_settings(dashen_account_number='')
    with pytest.raises(ValueError, match='DASHEN_ACCOUNT_NUMBER'):
        s.effective_dashen_account_number


# --- PROD-05: secrets guardrails --------------------------------------------

def test_production_requires_provider_key_encryption_secret():
    s = _prod_settings(provider_key_encryption_secret='')
    with pytest.raises(ValueError, match='PROVIDER_KEY_ENCRYPTION_SECRET'):
        s.effective_provider_key_encryption_secret


def test_production_provider_key_encryption_secret_min_length():
    s = _prod_settings(provider_key_encryption_secret='12345678')
    with pytest.raises(ValueError, match='at least 32 characters'):
        s.effective_provider_key_encryption_secret


def test_production_database_url_required():
    """Pins the pre-existing DATABASE_URL guard."""
    s = _prod_settings(database_url='')
    with pytest.raises(ValueError, match='DATABASE_URL'):
        s.effective_database_url


def test_production_jwt_secret_required():
    """Pins the pre-existing JWT_SECRET_KEY guard."""
    s = _prod_settings(jwt_secret_key='')
    with pytest.raises(ValueError, match='JWT_SECRET_KEY'):
        s.effective_jwt_secret_key


def test_production_jwt_secret_min_length():
    """Pins the pre-existing JWT_SECRET_KEY minimum-length guard."""
    s = _prod_settings(jwt_secret_key='12345678')
    with pytest.raises(ValueError, match='at least 32 characters'):
        s.effective_jwt_secret_key


def test_development_defaults_skip_guards():
    s = Settings(_env_file=None, app_env='development')
    assert s.effective_receipt_extraction_mode == 'mock'
    assert s.effective_cbe_account_holder == ''
    assert s.effective_cbe_account_number == ''
    assert s.effective_dashen_account_holder == ''
    assert s.effective_dashen_account_number == ''
    assert s.effective_provider_key_encryption_secret == ''
    assert s.effective_database_url == 'sqlite+pysqlite:///:memory:'


def test_fernet_binding_uses_effective_encryption_secret(monkeypatch):
    """The provider-key Fernet must seed from the PROD-05 effective property:
    a 32+ char production secret round-trips; a different secret cannot
    decrypt; an empty production secret raises ValueError at encrypt time."""
    import app.services.security as security_mod

    from cryptography.fernet import InvalidToken

    prod = _prod_settings()
    monkeypatch.setattr(security_mod, 'settings', prod)

    token = security_mod.encrypt_provider_key('sk-test-1234')
    assert security_mod.decrypt_provider_key(token) == 'sk-test-1234'

    other = _prod_settings(provider_key_encryption_secret='z' * 40)
    monkeypatch.setattr(security_mod, 'settings', other)
    with pytest.raises(InvalidToken):
        security_mod.decrypt_provider_key(token)

    empty = _prod_settings(provider_key_encryption_secret='')
    monkeypatch.setattr(security_mod, 'settings', empty)
    with pytest.raises(ValueError, match='PROVIDER_KEY_ENCRYPTION_SECRET'):
        security_mod.encrypt_provider_key('sk-test-1234')
