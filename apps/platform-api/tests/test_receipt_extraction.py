import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.provider_key import ProviderApiKey
from app.models.receipt_extraction import ReceiptExtraction
from app.services.billing.receipt_extraction import (
    EXTRACTION_FIELDS,
    LOW_CONFIDENCE_THRESHOLD,
    ZERO_CONFIDENCE_WARNING,
    resolve_extraction_key,
)
from app.services.security import encrypt_provider_key, mask_provider_key
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, payload: dict | None = None, mock_json: str | None = None):
    data = {}
    if mock_json is not None:
        data['mock_extraction'] = mock_json
    elif payload is not None:
        data['mock_extraction'] = json.dumps(payload)
    return client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data=data,
    )


def _queue_item(client: TestClient, token: str) -> dict:
    resp = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    return resp.json()[0]


def test_no_key_returns_zero_confidence_and_flag(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice(with_ai_key=False)
    assert _upload(client, token, payload=mock_extraction_payload()).status_code == 200
    item = _queue_item(client, token)
    assert item['has_zero_confidence'] is True
    assert item['zero_confidence_warning'] == ZERO_CONFIDENCE_WARNING
    assert all(value is None for value in item['extracted_fields'].values())


def test_resolve_key_prefers_active_preferred_key(
    db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    second = ProviderApiKey(
        organization_id=org.id,
        created_by_user_id=org.id,
        provider_name='mock',
        key_name='secondary',
        masked_key=mask_provider_key('sk-mock-second-1234'),
        encrypted_key=encrypt_provider_key('sk-mock-second-1234'),
        status='active',
    )
    db_session.add(second)
    db_session.commit()
    db_session.refresh(org)
    key = resolve_extraction_key(db_session, org)
    assert key is not None
    assert key.key_name == 'primary'
    assert str(key.id) == org.preferred_ai_key_id


def test_revoked_preferred_key_falls_back(
    db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    key = db_session.get(ProviderApiKey, org.preferred_ai_key_id)
    key.status = 'revoked'
    db_session.add(key)
    db_session.commit()
    assert resolve_extraction_key(db_session, org) is None


def test_mock_adapter_returns_eight_fields(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, payload=mock_extraction_payload()).status_code == 200

    extraction = db_session.execute(
        select(ReceiptExtraction).where(ReceiptExtraction.receipt_id.isnot(None))
    ).scalars().one()
    assert set(extraction.fields.keys()) == set(EXTRACTION_FIELDS)
    assert set(extraction.confidence.keys()) == set(EXTRACTION_FIELDS)
    assert extraction.provider_name == 'mock'
    assert extraction.fields['sender_name'] == 'Mulugeta Tesfaye'
    assert extraction.fields['transfer_amount'] == '4520.00'


def test_extraction_persists_row_and_audits(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, payload=mock_extraction_payload()).status_code == 200

    extraction = db_session.execute(
        select(ReceiptExtraction).where(ReceiptExtraction.receipt_id.isnot(None))
    ).scalars().one()
    assert extraction.provider_name == 'mock'
    assert extraction.key_id == org.preferred_ai_key_id

    events = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.extraction_completed')
    ).scalars().all()
    assert len(events) == 1
    assert events[0].payload['provider_name'] == 'mock'
    assert events[0].payload['has_key'] is True
    assert events[0].payload['error'] is None


def test_low_confidence_fields_flagged_below_threshold(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    payload = mock_extraction_payload()
    payload['confidence']['sender_name'] = 0.4
    payload['confidence']['transfer_amount'] = 0.59
    assert _upload(client, token, payload=payload).status_code == 200

    item = _queue_item(client, token)
    assert 'sender_name' in item['low_confidence_fields']
    assert 'transfer_amount' in item['low_confidence_fields']
    assert 'reference_number' not in item['low_confidence_fields']
    assert LOW_CONFIDENCE_THRESHOLD == 0.60


def test_adapter_error_degrades_to_zero_confidence(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    unknown = ProviderApiKey(
        organization_id=org.id,
        created_by_user_id=org.id,
        provider_name='unknown-provider',
        key_name='weird',
        masked_key=mask_provider_key('sk-unknown-1234567890'),
        encrypted_key=encrypt_provider_key('sk-unknown-1234567890'),
        status='active',
    )
    db_session.add(unknown)
    db_session.commit()
    org.preferred_ai_key_id = unknown.id
    org.preferred_ai_provider = 'unknown-provider'
    db_session.add(org)
    db_session.commit()

    assert _upload(client, token, payload=mock_extraction_payload()).status_code == 200
    item = _queue_item(client, token)
    assert item['has_zero_confidence'] is True

    extraction = db_session.execute(
        select(ReceiptExtraction).where(ReceiptExtraction.receipt_id.isnot(None))
    ).scalars().one()
    assert extraction.error_message is not None
    assert extraction.provider_name is None


def test_extraction_never_fails_upload(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    # Malformed sidecar (missing 'fields'/'confidence') -> zero confidence,
    # but the upload itself succeeds.
    resp = _upload(client, token, payload={'bogus': True})
    assert resp.status_code == 200
