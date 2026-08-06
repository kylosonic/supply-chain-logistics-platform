"""Reversal API surface (blueprint §6): audit list, per-receipt audit
events with server-side actions, undo/reverse endpoints, the customer
reversal-status surface, and route-registration no-conflicts."""

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.user import User
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(
    client: TestClient,
    token: str,
    *,
    amount: str = '4520.00',
    ref: str,
    sender: str = 'Mulugeta Tesfaye',
):
    payload = mock_extraction_payload(
        fields={
            'sender_name': sender,
            'sender_account_number': '1000123456',
            'receiver_account_number': '1000134567890',
            'receiver_name': 'FreightPilot PLC',
            'transfer_amount': amount,
            'transfer_date': '2026-08-01',
            'reference_number': ref,
            'bank_identifier': 'cbe',
        }
    )
    return client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )


def _verify(client: TestClient, token: str, receipt_id: str):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json={'verdict': 'verify', 'trusted_payer_action': 'verified_once'},
    )


def test_audit_list_admin_only_403_for_operator_viewer(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()

    operator = db_session.execute(select(User).where(User.username == 'operator')).scalar_one()
    viewer = db_session.execute(select(User).where(User.username == 'viewer')).scalar_one()
    db_session.add_all(
        [
            OrganizationMembership(organization_id=org.id, user_id=operator.id, role='operator', is_active=True),
            OrganizationMembership(organization_id=org.id, user_id=viewer.id, role='viewer', is_active=True),
        ]
    )
    db_session.commit()
    op_token = client.post(
        '/api/v1/auth/login', json={'username': 'operator', 'password': 'operator12345'}
    ).json()['access_token']
    viewer_token = client.post(
        '/api/v1/auth/login', json={'username': 'viewer', 'password': 'viewer12345'}
    ).json()['access_token']

    assert client.get('/api/v1/receipts/audit', headers={'Authorization': f'Bearer {op_token}'}).status_code == 403
    assert client.get('/api/v1/receipts/audit', headers={'Authorization': f'Bearer {viewer_token}'}).status_code == 403
    # The audit-events surface is gated the same way.
    assert client.get(
        '/api/v1/receipts/00000000-0000-0000-0000-000000000000/audit-events',
        headers={'Authorization': f'Bearer {viewer_token}'},
    ).status_code == 403


def test_audit_list_returns_availability(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt, force_window
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-A1')

    resp = client.get('/api/v1/receipts/audit', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row['id'] == receipt_id
    assert row['organization_id'] == str(org.id)
    assert row['organization_name'] == org.name
    assert row['invoice_number'] == 'INV-000100'
    assert row['amount_etb'] == '4520.00'
    assert row['undo_available'] is True
    assert row['reverse_available'] is False
    assert row['undo_available_until'] is not None

    force_window(receipt_id, 25)
    rows = client.get('/api/v1/receipts/audit', headers={'Authorization': f'Bearer {token}'}).json()
    row = rows[0]
    assert row['undo_available'] is False
    assert row['reverse_available'] is True


def test_audit_events_per_receipt_with_actions(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt, force_window
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-A2')

    resp = client.get(
        f'/api/v1/receipts/{receipt_id}/audit-events', headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    events = resp.json()
    types = [e['event_type'] for e in events]
    assert 'receipts.uploaded' in types
    assert 'receipts.verified' in types
    # Newest first (NB-18 timeline): the list is sorted by created_at DESC.
    timestamps = [e['created_at'] for e in events]
    assert timestamps == sorted(timestamps, reverse=True)
    # NB-19.1: the Undo/Reverse action is anchored on the verified record.
    verified_event = next(e for e in events if e['event_type'] == 'receipts.verified')
    assert verified_event['available_actions'] == ['undo']
    assert all(e['available_actions'] == [] for e in events if e is not verified_event)

    force_window(receipt_id, 25)
    events = client.get(
        f'/api/v1/receipts/{receipt_id}/audit-events', headers={'Authorization': f'Bearer {token}'}
    ).json()
    assert next(e for e in events if e['event_type'] == 'receipts.verified')['available_actions'] == ['reverse']

    # After a reversal, no actions are available (one reversal per receipt).
    client.post(
        f'/api/v1/receipts/{receipt_id}/reverse',
        headers={'Authorization': f'Bearer {token}'},
        json={'reason': 'Admin review'},
    )
    events = client.get(
        f'/api/v1/receipts/{receipt_id}/audit-events', headers={'Authorization': f'Bearer {token}'}
    ).json()
    assert 'receipts.reversed' in [e['event_type'] for e in events]
    assert all(e['available_actions'] == [] for e in events)


def test_undo_endpoint_happy_path_and_commit(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-A3')

    resp = client.post(
        f'/api/v1/receipts/{receipt_id}/undo',
        headers={'Authorization': f'Bearer {token}'},
        json={'note': 'wrong account'},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['receipt_id'] == receipt_id
    assert body['reversal_status'] == 'undo'
    assert body['reversal_note'] == 'wrong account'
    assert body['restored_balance_etb'] == '4520.00'
    assert body['message'] is None  # undo carries no customer message

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == 4520
    audit = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.undo',
            AuditEvent.entity_id == str(receipt_id),
        )
    ).scalars().one()
    assert audit.payload['reversal_status'] == 'undo'


def test_reverse_endpoint_happy_path_and_message(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-A4')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()

    resp = client.post(
        f'/api/v1/receipts/{receipt_id}/reverse',
        headers={'Authorization': f'Bearer {token}'},
        json={'reason': 'Duplicate payment'},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['reversal_status'] == 'reversed'
    assert body['restored_balance_etb'] == '4520.00'
    assert 'has been reversed' in body['message']

    notification = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'receipt_reversed',
        )
    ).scalars().one()
    assert notification.message == body['message']


def test_customer_receipt_shows_reversal_status(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-A5')
    client.post(
        f'/api/v1/receipts/{receipt_id}/undo',
        headers={'Authorization': f'Bearer {token}'},
        json={},
    )

    rows = client.get('/api/v1/receipts', headers={'Authorization': f'Bearer {token}'}).json()
    row = next(r for r in rows if r['id'] == receipt_id)
    assert row['status'] == 'verified'  # decision #2: never leaves verified
    assert row['reversal_status'] == 'undo'


def test_route_registration_no_conflicts(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    """Both routers respond: /receipts/audit is NOT swallowed by any
    {receipt_id} pattern, and the legacy decision route still works."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-A6', amount='1000.00')  # keep an open balance

    resp = client.get('/api/v1/receipts/audit', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200

    resp = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200

    # A fresh receipt still routes through the legacy decision endpoint.
    assert _upload(client, token, ref='TXN-A7').status_code == 200
    rows = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    new_id = next(i['id'] for i in rows if i['extracted_fields']['reference_number'] == 'TXN-A7')
    assert _verify(client, token, new_id).status_code == 200
