"""PROD-03 contact-phone capture API tests (adjudication #5).

Pins: OWNER/ADMIN round-trip persistence + echo in SubscriptionRead; input
normalization (spaces/dashes/parens stripped, 9-15 digits with optional
leading +); 422 on invalid; 403 for non-owner/admin roles; the masked audit
event; and the end-to-end escalation path using the captured phone.
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.sms_message import SmsMessage
from app.models.user import User
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def test_update_contact_phone_round_trip(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, _invoice, token = make_paid_org_with_open_invoice()
    resp = client.post(
        '/api/v1/subscriptions/me/contact-phone',
        headers=_auth(token),
        json={'contact_phone': '+251911123456'},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['contact_phone'] == '+251911123456'

    db_session.refresh(org)
    assert org.contact_phone == '+251911123456'


def test_update_contact_phone_normalizes_input(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, _invoice, token = make_paid_org_with_open_invoice()
    resp = client.post(
        '/api/v1/subscriptions/me/contact-phone',
        headers=_auth(token),
        json={'contact_phone': '+251 91 123 4567'},
    )
    assert resp.status_code == 200
    assert resp.json()['contact_phone'] == '+251911234567'

    db_session.refresh(org)
    assert org.contact_phone == '+251911234567'


def test_update_contact_phone_rejects_invalid(
    client: TestClient, make_paid_org_with_open_invoice
):
    _org, _invoice, token = make_paid_org_with_open_invoice()
    resp = client.post(
        '/api/v1/subscriptions/me/contact-phone',
        headers=_auth(token),
        json={'contact_phone': 'not-a-phone'},
    )
    assert resp.status_code == 422


def test_update_contact_phone_requires_owner_or_admin(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, viewer_token
):
    org, _invoice, token = make_paid_org_with_open_invoice()
    viewer = db_session.execute(select(User).where(User.username == 'viewer')).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=org.id, user_id=viewer.id, role='viewer', is_active=True
        )
    )
    db_session.commit()

    resp = client.post(
        '/api/v1/subscriptions/me/contact-phone',
        headers=_auth(viewer_token),
        json={'contact_phone': '+251911000099'},
    )
    assert resp.status_code == 403


def test_update_contact_phone_audit_event(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, _invoice, token = make_paid_org_with_open_invoice()
    resp = client.post(
        '/api/v1/subscriptions/me/contact-phone',
        headers=_auth(token),
        json={'contact_phone': '+251911123456'},
    )
    assert resp.status_code == 200

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'organization.contact_phone_updated')
    ).scalars().one()
    assert event.organization_id == org.id
    assert event.actor_user_id is not None
    assert event.payload['contact_phone'] == '+25***56'  # masked, never the raw number
    assert '+251911123456' not in event.payload['contact_phone']


def test_escalation_uses_captured_phone(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, _invoice, token = make_paid_org_with_open_invoice()
    resp = client.post(
        '/api/v1/subscriptions/me/contact-phone',
        headers=_auth(token),
        json={'contact_phone': '+251 91 987 6543'},
    )
    assert resp.status_code == 200

    payload = mock_extraction_payload(
        fields={
            'sender_name': 'Mulugeta Tesfaye',
            'sender_account_number': '1000123456',
            'receiver_account_number': '1000134567890',
            'receiver_name': 'FreightPilot PLC',
            'transfer_amount': '4520.00',
            'transfer_date': '2026-08-01',
            'reference_number': 'TXN-CP1',
            'bank_identifier': 'cbe',
        }
    )
    resp = client.post(
        '/api/v1/receipts/upload',
        headers=_auth(token),
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )
    assert resp.status_code == 200
    rows = client.get('/api/v1/receipts/queue', headers=_auth(token)).json()
    receipt_id = next(
        item['id'] for item in rows if item['extracted_fields']['reference_number'] == 'TXN-CP1'
    )
    resp = client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers=_auth(token),
        json={'verdict': 'escalate', 'note': 'Question?'},
    )
    assert resp.status_code == 200

    row = db_session.execute(select(SmsMessage)).scalars().one()
    assert row.to_phone == '+251919876543'  # the normalized captured value
