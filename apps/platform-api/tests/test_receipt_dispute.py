import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dispute_thread import DisputeThread
from app.models.notification import Notification
from app.models.payment_receipt import PaymentReceipt
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, ref: str):
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


def _dispute(client: TestClient, token: str, receipt_id: str, text: str) -> object:
    return client.post(
        f'/api/v1/receipts/{receipt_id}/dispute',
        headers={'Authorization': f'Bearer {token}'},
        json={'text': text},
    )


def _reject_receipt(client: TestClient, token: str, ref: str) -> str:
    receipt_id = _queue_id(client, token, ref)
    assert _decision(client, token, receipt_id, {'verdict': 'reject_illegible'}).status_code == 200
    return receipt_id


def test_dispute_only_on_rejected_receipt_409_otherwise(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS1').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-DS1')
    resp = _dispute(client, token, receipt_id, 'This is my payment!')
    assert resp.status_code == 409


def test_dispute_converts_rejection_to_escalation_with_label(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS2').status_code == 200
    receipt_id = _reject_receipt(client, token, 'TXN-DS2')

    resp = _dispute(client, token, receipt_id, 'The reference is correct, please recheck.')
    assert resp.status_code == 200

    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.status == 'escalated'

    queue = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    item = next(row for row in queue if row['id'] == receipt_id)
    assert item['status'] == 'escalated'
    assert item['dispute_text'] == 'The reference is correct, please recheck.'
    assert item['dispute_status'] == 'open'


def test_dispute_thread_persists_text(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS3').status_code == 200
    receipt_id = _reject_receipt(client, token, 'TXN-DS3')
    assert _dispute(client, token, receipt_id, 'Please verify again.').status_code == 200

    thread = db_session.execute(
        select(DisputeThread).where(DisputeThread.receipt_id == receipt_id)
    ).scalars().one()
    assert thread.dispute_text == 'Please verify again.'
    assert thread.status == 'open'
    assert thread.submitted_by_user_id is not None


def test_workspace_stays_locked_during_dispute(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS4').status_code == 200
    receipt_id = _reject_receipt(client, token, 'TXN-DS4')
    assert _dispute(client, token, receipt_id, 'Dispute!').status_code == 200

    db_session.refresh(org)
    assert org.billing_phase == 'grace'


def test_dispute_resolution_verify_credits_and_unlocks(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS5').status_code == 200
    receipt_id = _reject_receipt(client, token, 'TXN-DS5')
    assert _dispute(client, token, receipt_id, 'This was really my transfer.').status_code == 200

    resp = _decision(client, token, receipt_id, {'verdict': 'verify'})
    assert resp.status_code == 200

    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.status == 'verified'
    thread = db_session.execute(
        select(DisputeThread).where(DisputeThread.receipt_id == receipt_id)
    ).scalars().one()
    assert thread.status == 'resolved'
    assert thread.resolution == 'verify'

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == 0
    assert invoice.status == 'paid'
    db_session.refresh(org)
    assert org.billing_phase == 'active'

    verified = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'receipt_verified',
        )
    ).scalars().all()
    assert len(verified) == 1


def test_dispute_resolution_maintain_rejection_banner(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS6').status_code == 200
    receipt_id = _reject_receipt(client, token, 'TXN-DS6')
    assert _dispute(client, token, receipt_id, 'I disagree.').status_code == 200

    resp = _decision(client, token, receipt_id, {'verdict': 'reject_illegible'})
    assert resp.status_code == 200

    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.status == 'rejected'
    thread = db_session.execute(
        select(DisputeThread).where(DisputeThread.receipt_id == receipt_id)
    ).scalars().one()
    assert thread.status == 'resolved'
    assert thread.resolution == 'maintain_rejection'

    banner = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'dispute_resolved',
        )
    ).scalars().all()
    assert len(banner) == 1
    assert banner[0].payload['resolution'] == 'maintain_rejection'


def test_second_dispute_on_same_receipt_409(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DS7').status_code == 200
    receipt_id = _reject_receipt(client, token, 'TXN-DS7')
    assert _dispute(client, token, receipt_id, 'First dispute.').status_code == 200
    resp = _dispute(client, token, receipt_id, 'Second dispute.')
    assert resp.status_code == 409
