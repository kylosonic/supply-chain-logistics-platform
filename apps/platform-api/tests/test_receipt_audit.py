import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.sms_message import SmsMessage
from app.models.wallet_credit import WalletCredit
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, amount: str = '4520.00', ref: str, sender: str = 'Mulugeta Tesfaye'):
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


def _queue_id(client: TestClient, token: str, ref: str) -> str:
    rows = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    return next(item['id'] for item in rows if item['extracted_fields']['reference_number'] == ref)


def _decision(client: TestClient, token: str, receipt_id: str, body: dict) -> object:
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json=body,
    )


def _audit(db: Session, org_id, event_type: str) -> AuditEvent:
    return db.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == event_type,
            AuditEvent.organization_id == org_id,
        )
    ).scalars().one()


def test_verified_audit_carries_full_field_set(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-AUD1').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-AUD1')
    assert _decision(
        client, token, receipt_id,
        {'verdict': 'verify', 'admin_note': 'looks good', 'trusted_payer_action': 'verified_once'},
    ).status_code == 200

    event = _audit(db_session, org.id, 'receipts.verified')
    payload = event.payload
    assert payload['invoice_number'] == 'INV-000100'
    assert payload['reference_number'] == 'TXN-AUD1'
    assert payload['sender_name'] == 'Mulugeta Tesfaye'
    assert payload['amount_etb'] == '4520.00'
    assert payload['balance_before_etb'] == '4520.00'
    assert payload['decision'] == 'verified'
    assert payload['credit_delta_etb'] == '4520.00'
    assert payload['note'] == 'looks good'
    assert payload['trusted_payer_action'] == 'verified_once'
    assert payload['wallet_credit_etb'] == '0.00'
    assert payload['large_surplus_decision'] is None


def test_rejected_audit_reason(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-AUD2').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-AUD2')
    assert _decision(client, token, receipt_id, {'verdict': 'reject_illegible'}).status_code == 200

    event = _audit(db_session, org.id, 'receipts.rejected')
    assert event.payload['verdict'] == 'reject_illegible'
    assert event.payload['reference_number'] == 'TXN-AUD2'
    assert 'couldn' in event.payload['reason'].lower() or "couldn't" in event.payload['reason']


def test_escalation_audit_note(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-AUD3').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-AUD3')
    assert _decision(client, token, receipt_id, {'verdict': 'escalate', 'note': 'Ambiguous sender — confirm identity.'}).status_code == 200

    event = _audit(db_session, org.id, 'receipts.escalated')
    assert event.payload['note'] == 'Ambiguous sender — confirm identity.'
    assert event.payload['reference_number'] == 'TXN-AUD3'


def test_wallet_credit_audit_chain(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    """receipts.uploaded -> receipts.verified -> sms-free wallet chain."""
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='5000.00', ref='TXN-AUD4').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-AUD4')
    assert _decision(client, token, receipt_id, {'verdict': 'verify'}).status_code == 200

    uploaded = _audit(db_session, org.id, 'receipts.uploaded')
    assert uploaded.payload['file_sha256']
    assert uploaded.payload['invoice_number'] == 'INV-000100'

    verified = _audit(db_session, org.id, 'receipts.verified')
    assert verified.payload['wallet_credit_etb'] == '480.00'

    wallet_rows = db_session.execute(
        select(WalletCredit).where(WalletCredit.organization_id == org.id)
    ).scalars().all()
    assert len(wallet_rows) == 1

    # No SMS on verification.
    assert db_session.execute(select(SmsMessage)).scalars().all() == []


def test_audit_actor_is_admin_user(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-AUD5').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-AUD5')
    assert _decision(client, token, receipt_id, {'verdict': 'verify'}).status_code == 200

    event = _audit(db_session, org.id, 'receipts.verified')
    assert event.actor_user_id is not None

    from app.models.user import User

    actor = db_session.get(User, event.actor_user_id)
    assert actor is not None
    assert actor.email == f'owner-{invoice.invoice_number.lower()}@receiptco.com'
