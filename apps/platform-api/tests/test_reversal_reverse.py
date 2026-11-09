"""Post-24h Reverse (TECH-18/20 / NB-20): mandatory reason + customer notice.

Reverse requires a non-blank reason (422, NB-20.2), writes the EXACT
NB-20.3 in-product Notification copy (decision #8), creates a DISTINCT
``receipts.reversed`` audit record (NB-20.4), performs NO automatic refund
and NO SMS (NB-20.5), and is server-guarded against the within-24h window
(409 — use Undo).
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.notification import Notification
from app.models.payment_receipt import PaymentReceipt
from app.models.sms_message import SmsMessage
from app.models.wallet_credit import WalletCredit


def _reverse(client: TestClient, token: str, receipt_id: str, reason: str = 'Duplicate payment received'):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/reverse',
        headers={'Authorization': f'Bearer {token}'},
        json={'reason': reason},
    )


def test_reverse_requires_reason_422_when_blank(
    client: TestClient,
    db_session: Session,
    make_paid_org_with_open_invoice,
    verify_receipt,
    monkeypatch,
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R1')
    fixed = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = fixed - timedelta(hours=25)
    db_session.commit()
    monkeypatch.setattr('app.services.billing.reversals.core._now', lambda: fixed)

    resp = _reverse(client, token, receipt_id, reason='   ')
    assert resp.status_code == 422


def test_reverse_after_24h_restores_balance_and_reopens(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R2')
    force = datetime.now(UTC)
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = force - timedelta(hours=25)
    db_session.commit()

    resp = _reverse(client, token, receipt_id, reason='Funds returned by bank')
    assert resp.status_code == 200
    body = resp.json()
    assert body['reversal_status'] == 'reversed'
    assert body['restored_balance_etb'] == '4520.00'
    assert body['wallet_voided_etb'] == '0.00'

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('4520.00')
    assert invoice.status == 'issued'


def test_reverse_writes_exact_customer_message(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt, monkeypatch
):
    """The Notification row carries the EXACT NB-20.3 copy (decision #8):
    amount/date from the verified audit payload, reason interpolated."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R3')
    fixed = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)  # decided_at -> 2026-08-05 in Addis
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = fixed - timedelta(hours=25)
    db_session.commit()
    monkeypatch.setattr('app.services.billing.reversals.core._now', lambda: fixed)

    reason = 'Duplicate payment received'
    resp = _reverse(client, token, receipt_id, reason=reason)
    assert resp.status_code == 200

    expected = (
        'Your payment of 4520.00 ETB credited on 05 Aug 2026 against Invoice #INV-000100 '
        'has been reversed. Reason: Duplicate payment received. '
        'Please contact us if you believe this is in error. Your workspace may be locked.'
    )
    notification = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'receipt_reversed',
        )
    ).scalars().one()
    assert notification.message == expected
    # sqlite round-trips tz-aware datetimes as naive — normalize for the comparison.
    expires = notification.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    assert expires == fixed + timedelta(days=3)
    assert resp.json()['message'] == expected

    # NO SMS on reverse.
    assert db_session.execute(select(SmsMessage)).scalars().all() == []


def test_reverse_creates_distinct_audit_record(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R4')

    verified = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.verified',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().one()
    original_payload = json.dumps(verified.payload, sort_keys=True)

    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()

    reason = 'Receipt was from an unverified sender'
    resp = _reverse(client, token, receipt_id, reason=reason)
    assert resp.status_code == 200

    # Original verified record untouched.
    db_session.refresh(verified)
    assert json.dumps(verified.payload, sort_keys=True) == original_payload

    # DISTINCT receipts.reversed record with the mandatory note.
    reversed_events = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.reversed',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().all()
    assert len(reversed_events) == 1
    payload = reversed_events[0].payload
    assert payload['decision'] == 'reversed'
    assert payload['note'] == reason
    assert payload['notification_sent'] is True
    assert payload['credit_delta_etb'] == '-4520.00'
    assert payload['restored_balance_etb'] == '4520.00'
    assert payload['original_verified_event_id'] == str(verified.id)


def test_reverse_no_automatic_refund(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R5')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()
    wallet_before = len(
        db_session.execute(
            select(WalletCredit).where(WalletCredit.organization_id == org.id)
        ).scalars().all()
    )

    resp = _reverse(client, token, receipt_id, reason='No refund on file')
    assert resp.status_code == 200

    # NO wallet row created.
    wallet_after = len(
        db_session.execute(
            select(WalletCredit).where(WalletCredit.organization_id == org.id)
        ).scalars().all()
    )
    assert wallet_after == wallet_before
    assert db_session.execute(select(SmsMessage)).scalars().all() == []


def test_reverse_inside_24h_409_forces_undo(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R6')  # decided_at = now -> inside window

    resp = _reverse(client, token, receipt_id, reason='Too soon')
    assert resp.status_code == 409
    assert 'Undo within 24 hours' in resp.json()['detail']


def test_reverse_twice_409(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R7')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()

    assert _reverse(client, token, receipt_id, reason='First reversal').status_code == 200
    resp = _reverse(client, token, receipt_id, reason='Second reversal')  # one reversal per receipt
    assert resp.status_code == 409
    assert 'already been reversed' in resp.json()['detail'].lower()


def test_reverse_re_locks_workspace(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-R8')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()
    db_session.refresh(org)
    assert org.billing_phase == 'active'

    resp = _reverse(client, token, receipt_id, reason='Reversal per policy')
    assert resp.status_code == 200

    db_session.refresh(org)
    assert org.billing_phase in ('grace', 'hard_locked')  # NB-20.5 may be locked
