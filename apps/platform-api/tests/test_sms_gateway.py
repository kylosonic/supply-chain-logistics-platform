"""PROD-03 SMS gateway adapter tests (adjudication #3 — provider-agnostic
generic REST POST-JSON gateway).

Pins: unconfigured deployments keep rows ``queued`` (regression pin for the
9 escalation tests); a configured gateway marks rows ``sent`` with
``provider_name='generic_http'``; gateway failures fail soft — the row goes
``failed`` with a truncated error and the escalation path/banner is
unaffected; the wire payload uses the configured sender name + the org's
captured phone.
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification
from app.models.sms_message import SmsMessage
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _escalate(client: TestClient, token: str, ref: str) -> object:
    payload = mock_extraction_payload(
        fields={
            'sender_name': 'Mulugeta Tesfaye',
            'sender_account_number': '1000123456',
            'receiver_account_number': '1000134567890',
            'receiver_name': 'FreightPilot PLC',
            'transfer_amount': '4520.00',
            'transfer_date': '2026-08-01',
            'reference_number': ref,
            'bank_identifier': 'cbe',
        }
    )
    resp = client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )
    assert resp.status_code == 200
    rows = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    receipt_id = next(
        item['id'] for item in rows if item['extracted_fields']['reference_number'] == ref
    )
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json={'verdict': 'escalate', 'note': 'Question?'},
    )


def test_unconfigured_gateway_keeps_row_queued(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    monkeypatch,
):
    """Regression pin: no URL/key -> row stays queued (dev/test parity)."""
    org, _invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000001'
    db_session.add(org)
    db_session.commit()
    monkeypatch.setattr(settings, 'sms_gateway_url', '')
    monkeypatch.setattr(settings, 'sms_gateway_api_key', '')

    resp = _escalate(client, token, 'TXN-GW1')
    assert resp.status_code == 200

    row = db_session.execute(select(SmsMessage)).scalars().one()
    assert row.status == 'queued'
    assert row.provider_name is None
    assert row.to_phone == '+251911000001'


def test_configured_gateway_marks_row_sent(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    monkeypatch,
):
    from app.services.billing import sms as sms_module

    org, _invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000002'
    db_session.add(org)
    db_session.commit()
    monkeypatch.setattr(settings, 'sms_gateway_url', 'https://sms.example.test/send')
    monkeypatch.setattr(settings, 'sms_gateway_api_key', 'test-key')

    captured: list[dict] = []

    def fake_post(payload: dict) -> dict:
        captured.append(payload)
        return {'id': 'gw-msg-42'}

    monkeypatch.setattr(sms_module, '_post_to_gateway', fake_post)

    resp = _escalate(client, token, 'TXN-GW2')
    assert resp.status_code == 200
    assert captured

    row = db_session.execute(select(SmsMessage)).scalars().one()
    assert row.status == 'sent'
    assert row.provider_name == 'generic_http'
    assert row.sent_at is not None
    assert row.gateway_message_id == 'gw-msg-42'


def test_gateway_failure_fails_soft(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    monkeypatch,
):
    from app.services.billing import sms as sms_module

    org, _invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000003'
    db_session.add(org)
    db_session.commit()
    monkeypatch.setattr(settings, 'sms_gateway_url', 'https://sms.example.test/send')
    monkeypatch.setattr(settings, 'sms_gateway_api_key', 'test-key')

    def boom(payload: dict) -> dict:
        raise RuntimeError('gateway timeout after 15s')

    monkeypatch.setattr(sms_module, '_post_to_gateway', boom)

    resp = _escalate(client, token, 'TXN-GW3')
    assert resp.status_code == 200  # dispatch never raises into the decision path

    row = db_session.execute(select(SmsMessage)).scalars().one()
    assert row.status == 'failed'
    assert row.error_message is not None
    assert 'gateway timeout' in row.error_message

    notification = db_session.execute(
        select(Notification).where(Notification.kind == 'receipt_escalated')
    ).scalars().one()
    assert notification.organization_id == org.id  # in-product banner still fires


def test_gateway_payload_uses_sender_name_and_phone(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    monkeypatch,
):
    from app.services.billing import sms as sms_module

    org, _invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000004'
    db_session.add(org)
    db_session.commit()
    monkeypatch.setattr(settings, 'sms_gateway_url', 'https://sms.example.test/send')
    monkeypatch.setattr(settings, 'sms_gateway_api_key', 'test-key')
    monkeypatch.setattr(settings, 'sms_sender_name', 'FreightPilot')

    captured: list[dict] = []
    monkeypatch.setattr(sms_module, '_post_to_gateway', lambda payload: captured.append(payload) or {'id': None})

    resp = _escalate(client, token, 'TXN-GW4')
    assert resp.status_code == 200
    assert captured

    payload = captured[0]
    assert payload['to'] == org.contact_phone
    assert payload['sender'] == settings.sms_sender_name
    assert payload['brand'] == settings.sms_brand_name
    assert 'FreightPilot' in payload['text']
