import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.notification import Notification
from app.models.payment_receipt import PaymentReceipt
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, amount: str, ref: str):
    payload = mock_extraction_payload(
        fields={
            'sender_name': 'Mulugeta Tesfaye',
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


def _verify(client: TestClient, token: str, receipt_id: str) -> object:
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json={'verdict': 'verify'},
    )


def _pending_receipt(client: TestClient, token: str, ref: str) -> str:
    rows = client.get('/api/v1/receipts', headers={'Authorization': f'Bearer {token}'}).json()
    return next(row['id'] for row in rows if row['reference_number'] == ref and row['status'] == 'pending')


def test_duplicate_reference_across_organizations_hard_rejects(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org_a, _, token_a = make_paid_org_with_open_invoice(invoice_number='INV-000100')
    org_b, _, token_b = make_paid_org_with_open_invoice(invoice_number='INV-000200')

    assert _upload(client, token_a, amount='4520.00', ref='TXN-X1').status_code == 200
    assert _verify(client, token_a, _pending_receipt(client, token_a, 'TXN-X1')).status_code == 200

    assert _upload(client, token_b, amount='4520.00', ref='TXN-X1').status_code == 200
    dup = db_session.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.reference_number == 'TXN-X1',
            PaymentReceipt.status == 'rejected',
        )
    ).scalars().one()
    assert dup.organization_id == org_b.id
    assert dup.verdict == 'reject_duplicate'
    assert dup.invoice_id is None


def test_duplicate_reference_across_invoices_hard_rejects(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-X2').status_code == 200
    assert _verify(client, token, _pending_receipt(client, token, 'TXN-X2')).status_code == 200

    assert _upload(client, token, amount='4520.00', ref='TXN-X2').status_code == 200
    dups = db_session.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.reference_number == 'TXN-X2',
            PaymentReceipt.status == 'rejected',
        )
    ).scalars().all()
    assert len(dups) == 1


def test_duplicate_rejection_banner_copy_exact(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-X3').status_code == 200
    assert _verify(client, token, _pending_receipt(client, token, 'TXN-X3')).status_code == 200
    assert _upload(client, token, amount='4520.00', ref='TXN-X3').status_code == 200

    notification = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'receipt_rejected',
        )
    ).scalars().one()
    assert notification.message == (
        'Your receipt (ref TXN-X3) was rejected. Reason: This reference number has already been '
        'credited. Please upload a new receipt for your current invoice.'
    )
    assert notification.payload['verdict'] == 'reject_duplicate'
    assert notification.payload['can_reupload'] is True


def test_duplicate_fraud_flag_pair_in_audit(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org_a, _, token_a = make_paid_org_with_open_invoice(invoice_number='INV-000100')
    org_b, _, token_b = make_paid_org_with_open_invoice(invoice_number='INV-000200')

    assert _upload(client, token_a, amount='4520.00', ref='TXN-X4').status_code == 200
    assert _verify(client, token_a, _pending_receipt(client, token_a, 'TXN-X4')).status_code == 200
    original = db_session.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.reference_number == 'TXN-X4',
            PaymentReceipt.status == 'verified',
        )
    ).scalars().one()

    assert _upload(client, token_b, amount='4520.00', ref='TXN-X4').status_code == 200
    attempt = db_session.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.reference_number == 'TXN-X4',
            PaymentReceipt.status == 'rejected',
        )
    ).scalars().one()

    attempts = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.duplicate_attempt')
    ).scalars().all()
    flagged = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.duplicate_flagged')
    ).scalars().all()
    assert len(attempts) == 1
    assert len(flagged) == 1
    assert str(attempts[0].entity_id) == str(attempt.id)
    assert attempts[0].payload['original_receipt_id'] == str(original.id)
    assert str(flagged[0].entity_id) == str(original.id)
    assert flagged[0].payload['duplicate_receipt_id'] == str(attempt.id)


def test_second_verify_same_ref_409_and_forced_duplicate_reject(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    """Two pending receipts sharing a ref: only one can ever verify; the
    second verify hits the partial-unique backstop -> 409; the admin is
    forced to use reject_duplicate."""
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-X5').status_code == 200
    assert _upload(client, token, amount='4520.00', ref='TXN-X5').status_code == 200

    first = _pending_receipt(client, token, 'TXN-X5')
    second = client.get('/api/v1/receipts', headers={'Authorization': f'Bearer {token}'}).json()
    second = next(row['id'] for row in second if row['reference_number'] == 'TXN-X5' and row['status'] == 'pending' and row['id'] != first)

    assert _verify(client, token, first).status_code == 200
    resp = _verify(client, token, second)
    assert resp.status_code == 409
    assert 'already been credited' in resp.json()['detail']

    # Forced path: reject the duplicate explicitly.
    rejected = client.post(
        f'/api/v1/receipts/{second}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json={'verdict': 'reject_duplicate'},
    )
    assert rejected.status_code == 200
    receipt = db_session.get(PaymentReceipt, second)
    assert receipt.status == 'rejected'
    assert receipt.verdict == 'reject_duplicate'


def test_duplicate_attempt_does_not_create_queue_item(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-X6').status_code == 200
    assert _verify(client, token, _pending_receipt(client, token, 'TXN-X6')).status_code == 200
    assert _upload(client, token, amount='4520.00', ref='TXN-X6').status_code == 200

    queue = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    assert queue == []
