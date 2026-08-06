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
