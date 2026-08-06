"""PROD-02 production adapter tests — OpenAI-compatible chat-completions
extraction adapter + production mode guard (adjudication #2).

Pins: the `openai` registry branch normalizes a chat-completions response
into the canonical 8-field extraction contract; the adapter targets the
configured base URL; provider failures degrade to zero confidence without
failing the upload; `real` mode locks the mock adapter out; `zero_confidence`
mode never touches the provider seam; the dev/test mock adapter still works.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.provider_key import ProviderApiKey
from app.models.receipt_extraction import ReceiptExtraction
from app.services.billing.receipt_extraction import (
    EXTRACTION_FIELDS,
    ProviderAdapterError,
)
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _canned_chat_response() -> dict:
    """OpenAI chat-completions shape: model + choices[0].message.content JSON."""
    content = {
        'sender_name': 'Mulugeta Tesfaye',
        'sender_account_number': '1000123456',
        'receiver_account_number': '1000134567890',
        'receiver_name': 'FreightPilot PLC',
        'transfer_amount': '4520.00',
        'transfer_date': '2026-08-01',
        'reference_number': 'TXN-2001',
        'bank_identifier': 'cbe',
        'confidence': {name: 0.9 for name in EXTRACTION_FIELDS},
    }
    return {
        'model': 'gpt-4o-mini-2026-test',
        'choices': [{'message': {'content': json.dumps(content)}}],
    }


def _switch_key_to_openai(db_session: Session, org) -> ProviderApiKey:
    """Flip the fixture's active mock key to provider ``openai``."""
    key = db_session.get(ProviderApiKey, org.preferred_ai_key_id)
    key.provider_name = 'openai'
    db_session.add(key)
    db_session.commit()
    return key


def _queue_item(client: TestClient, token: str) -> dict:
    resp = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    return resp.json()[0]


def test_openai_adapter_normalizes_chat_completion_response(monkeypatch):
    from app.services.billing import receipt_extraction as rx

    monkeypatch.setattr(rx, '_post_chat_completion', lambda url, api_key, payload: _canned_chat_response())
    raw = rx._extract_with_provider('openai', 'sk-test', sample_receipt_bytes())
    fields, confidence, model_name = rx._validate_adapter_output(raw)

    assert set(fields) == set(EXTRACTION_FIELDS)
    assert fields['sender_name'] == 'Mulugeta Tesfaye'
    assert fields['transfer_amount'] == '4520.00'
    assert fields['bank_identifier'] == 'cbe'
    assert confidence['sender_name'] == 0.9
    assert all(0.0 <= score <= 1.0 for score in confidence.values())
    assert model_name == 'gpt-4o-mini-2026-test'


def test_openai_adapter_posts_to_configured_base_url(monkeypatch):
    from app.services.billing import receipt_extraction as rx

    calls: list[tuple[str, str, dict]] = []

    def record(url: str, api_key: str, payload: dict) -> dict:
        calls.append((url, api_key, payload))
        return _canned_chat_response()

    monkeypatch.setattr(rx, '_post_chat_completion', record)
    monkeypatch.setattr(settings, 'receipt_extraction_base_url', 'https://gateway.example.test/v1')

    rx._extract_with_provider('openai', 'sk-test', sample_receipt_bytes())

    url, api_key, payload = calls[0]
    assert url.startswith('https://gateway.example.test/v1')
    assert url.endswith('/chat/completions')
    assert api_key == 'sk-test'
    assert payload['model'] == settings.receipt_extraction_model
    user_msg = payload['messages'][-1]
    assert 'data:image/png;base64,' in user_msg['content'][-1]['image_url']['url']


def test_openai_adapter_error_degrades_to_zero_confidence(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    monkeypatch,
):
    from app.services.billing import receipt_extraction as rx

    org, _invoice, token = make_paid_org_with_open_invoice()
    _switch_key_to_openai(db_session, org)

    def boom(url: str, api_key: str, payload: dict) -> dict:
        raise ProviderAdapterError('simulated gateway failure')

    monkeypatch.setattr(rx, '_post_chat_completion', boom)

    resp = client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
    )
    assert resp.status_code == 200  # fail-soft preserved

    item = _queue_item(client, token)
    assert item['has_zero_confidence'] is True
    extraction = db_session.execute(
        select(ReceiptExtraction).where(ReceiptExtraction.receipt_id.isnot(None))
    ).scalars().one()
    assert extraction.error_message is not None
    assert extraction.provider_name is None


def test_real_mode_disables_mock_adapter(monkeypatch):
    """mock cannot leak into production mode — the registry refuses."""
    from app.services.billing import receipt_extraction as rx

    monkeypatch.setattr(settings, 'receipt_extraction_mode', 'real')
    with pytest.raises(ProviderAdapterError, match='mock adapter disabled'):
        rx._extract_with_provider('mock', 'sk-mock', sample_receipt_bytes())


def test_zero_confidence_mode_never_calls_provider(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    monkeypatch,
):
    from app.services.billing import receipt_extraction as rx

    org, _invoice, token = make_paid_org_with_open_invoice()
    _switch_key_to_openai(db_session, org)

    calls: list = []

    def record(url: str, api_key: str, payload: dict) -> dict:
        calls.append((url, api_key, payload))
        return _canned_chat_response()

    monkeypatch.setattr(rx, '_post_chat_completion', record)
    monkeypatch.setattr(settings, 'receipt_extraction_mode', 'zero_confidence')

    resp = client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
    )
    assert resp.status_code == 200
    assert calls == []  # provider seam never invoked

    item = _queue_item(client, token)
    assert item['has_zero_confidence'] is True
    assert all(value is None for value in item['extracted_fields'].values())

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.extraction_completed')
    ).scalars().one()
    assert event.payload['has_key'] is True
    assert event.payload['error'] == 'zero_confidence_mode'


def test_mock_adapter_still_works_in_test_mode(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    """Regression pin: default dev/test mode keeps the mock path canonical."""
    org, _invoice, token = make_paid_org_with_open_invoice()
    resp = client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(mock_extraction_payload())},
    )
    assert resp.status_code == 200
    extraction = db_session.execute(
        select(ReceiptExtraction).where(ReceiptExtraction.receipt_id.isnot(None))
    ).scalars().one()
    assert set(extraction.fields) == set(EXTRACTION_FIELDS)
    assert extraction.fields['sender_name'] == 'Mulugeta Tesfaye'
    assert extraction.provider_name == 'mock'
