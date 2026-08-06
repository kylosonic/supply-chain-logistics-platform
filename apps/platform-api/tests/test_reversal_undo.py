"""Silent Undo (TECH-18/19 / NB-18/19) — the within-24h correction window.

Server-enforced (decision #7): the window is evaluated against
``receipt.decided_at + 24h`` at every call; the boundary at exactly 24h is
Undo-eligible (``<=``). Undo writes NO customer notification (NB-19.3) and
its own ``receipts.undo`` audit record — the original ``receipts.verified``
event is NEVER mutated (NB-18.3).
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from tests.conftest import sample_receipt_bytes


def _undo(client: TestClient, token: str, receipt_id: str, note: str | None = None):
    body = {'note': note} if note is not None else {}
    return client.post(
        f'/api/v1/receipts/{receipt_id}/undo',
        headers={'Authorization': f'Bearer {token}'},
        json=body,
    )


def _audit_list(client: TestClient, token: str):
    resp = client.get('/api/v1/receipts/audit', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_undo_within_24h_restores_balance_and_reopens_invoice(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U1')
    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == 0
    assert invoice.status == 'paid'

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('4520.00')
    assert invoice.status == 'issued'


def test_undo_no_customer_notification(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U2')
    before = db_session.execute(
        select(func.count(Notification.id)).where(Notification.organization_id == org.id)
    ).scalar_one()

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    after = db_session.execute(
        select(func.count(Notification.id)).where(Notification.organization_id == org.id)
    ).scalar_one()
    assert before == after  # NB-19.3: undo writes NO notification


def test_undo_creates_own_audit_record_and_leaves_original_untouched(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U3')

    verified = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.verified',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().one()
    original_payload = json.dumps(verified.payload, sort_keys=True)
    original_id = verified.id

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    # Original event untouched (byte-identical payload, same row).
    db_session.refresh(verified)
    assert verified.id == original_id
    assert json.dumps(verified.payload, sort_keys=True) == original_payload

    # A NEW receipts.undo record exists (not an update).
    undo_events = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.undo',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().all()
    assert len(undo_events) == 1
    assert undo_events[0].entity_id == str(receipt_id)
    assert undo_events[0].payload['original_verified_event_id'] == str(original_id)
    assert undo_events[0].payload['decision'] == 'undo'
    assert undo_events[0].payload['credit_delta_etb'] == '-4520.00'
    assert undo_events[0].payload['restored_balance_etb'] == '4520.00'
    assert undo_events[0].payload['wallet_voided_etb'] == '0.00'


def test_undo_at_exactly_24h_boundary_eligible(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    verify_receipt,
    monkeypatch,
):
    """now == decided_at + 24h -> Undo still eligible (decision #7, <=)."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U4')
    fixed = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = fixed - timedelta(hours=24)
    db_session.commit()
    monkeypatch.setattr('app.services.billing.reversals.core._now', lambda: fixed)

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200


def test_undo_after_24h_server_guarded_409(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    verify_receipt,
    monkeypatch,
):
    """now == decided_at + 24h + 1s -> 409 even though the UI hid the button."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U5')
    fixed = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = fixed - timedelta(hours=24) - timedelta(seconds=1)
    db_session.commit()
    monkeypatch.setattr('app.services.billing.reversals.core._now', lambda: fixed)

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 409
    assert 'Undo window closed' in resp.json()['detail']


def test_undo_availability_flags_in_audit_payload(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt, force_window
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U6')

    rows = _audit_list(client, token)
    row = next(r for r in rows if r['id'] == receipt_id)
    assert row['undo_available'] is True
    assert row['reverse_available'] is False
    assert row['undo_available_until'] is not None
    assert row['reversal_status'] is None

    force_window(receipt_id, 25)  # past the 24h window
    rows = _audit_list(client, token)
    row = next(r for r in rows if r['id'] == receipt_id)
    assert row['undo_available'] is False
    assert row['reverse_available'] is True
    assert row['reversal_status'] is None


def test_undo_re_locks_workspace(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U7')
    db_session.refresh(org)
    assert org.billing_phase == 'active'

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    db_session.refresh(org)
    assert org.billing_phase in ('grace', 'hard_locked')  # NB-19.2 re-lock (read-only)


def test_undo_on_non_verified_409(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    payload = {
        'fields': {
            'sender_name': 'Mulugeta Tesfaye',
            'sender_account_number': '1000123456',
            'receiver_account_number': '1000134567890',
            'receiver_name': 'FreightPilot PLC',
            'transfer_amount': '4520.00',
            'transfer_date': '2026-08-01',
            'reference_number': 'TXN-U8',
            'bank_identifier': 'cbe',
        }
    }
    resp = client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )
    assert resp.status_code == 200
    receipt_id = resp.json()['receipt_id']

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 409
    assert 'verified' in resp.json()['detail'].lower()


def test_undo_twice_409(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U9')

    assert _undo(client, token, receipt_id).status_code == 200
    resp = _undo(client, token, receipt_id)  # one reversal per receipt (decision #9)
    assert resp.status_code == 409
    assert 'already been reversed' in resp.json()['detail'].lower()


def test_undo_optional_note_persisted_in_audit(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-U10')

    note = 'Wrong sender — bank confirms a different account'
    resp = _undo(client, token, receipt_id, note=note)
    assert resp.status_code == 200

    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.reversal_status == 'undo'
    assert receipt.reversal_note == note
    assert receipt.reversed_at is not None
    assert receipt.status == 'verified'  # decision #2: never leaves verified

    undo_event = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.undo',
            AuditEvent.entity_id == str(receipt_id),
        )
    ).scalars().one()
    assert undo_event.payload['note'] == note
