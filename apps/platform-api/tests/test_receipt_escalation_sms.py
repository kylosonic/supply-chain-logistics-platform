import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.sms_message import SmsMessage
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, amount: str = '4520.00', ref: str):
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


def _queue_id(client: TestClient, token: str, ref: str) -> str:
    rows = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    return next(item['id'] for item in rows if item['extracted_fields']['reference_number'] == ref)


def _decision(client: TestClient, token: str, receipt_id: str, body: dict) -> object:
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json=body,
    )


def test_escalate_enqueues_sms_row_queued(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000001'
    db_session.add(org)
    db_session.commit()

    assert _upload(client, token, ref='TXN-SMS1').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-SMS1')
    resp = _decision(client, token, receipt_id, {'verdict': 'escalate', 'note': 'Sender name is ambiguous.'})
    assert resp.status_code == 200

    rows = db_session.execute(select(SmsMessage)).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == 'queued'
    assert rows[0].to_phone == '+251911000001'
    assert rows[0].receipt_id is not None


def test_escalation_sms_body_under_160_chars(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000002'
    db_session.add(org)
    db_session.commit()
    assert _upload(client, token, ref='TXN-SMS2').status_code == 200
    assert _decision(client, token, _queue_id(client, token, 'TXN-SMS2'), {'verdict': 'escalate', 'note': 'Question?'}).status_code == 200

    row = db_session.execute(select(SmsMessage)).scalars().one()
    assert len(row.body) <= 160


def test_escalation_sms_no_receipt_specifics(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000003'
    db_session.add(org)
    db_session.commit()
    assert _upload(client, token, ref='TXN-SMS3').status_code == 200
    assert _decision(client, token, _queue_id(client, token, 'TXN-SMS3'), {'verdict': 'escalate', 'note': 'Question?'}).status_code == 200

    row = db_session.execute(select(SmsMessage)).scalars().one()
    assert 'FreightPilot' in row.body
    assert 'log in to your workspace to respond' in row.body
    assert 'TXN-SMS3' not in row.body
    assert '4520' not in row.body
    assert 'Mulugeta' not in row.body


def test_rejection_never_enqueues_sms(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000004'
    db_session.add(org)
    db_session.commit()
    assert _upload(client, token, ref='TXN-SMS4').status_code == 200
    assert _decision(client, token, _queue_id(client, token, 'TXN-SMS4'), {'verdict': 'reject_illegible'}).status_code == 200

    rows = db_session.execute(select(SmsMessage)).scalars().all()
    assert rows == []


def test_verification_never_enqueues_sms(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    org.contact_phone = '+251911000005'
    db_session.add(org)
    db_session.commit()
    assert _upload(client, token, ref='TXN-SMS5').status_code == 200
    assert _decision(client, token, _queue_id(client, token, 'TXN-SMS5'), {'verdict': 'verify'}).status_code == 200

    rows = db_session.execute(select(SmsMessage)).scalars().all()
    assert rows == []


def test_escalation_banner_with_question(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-SMS6').status_code == 200
    question = 'Your sender name does not match the account on file — can you confirm?'
    assert _decision(client, token, _queue_id(client, token, 'TXN-SMS6'), {'verdict': 'escalate', 'note': question}).status_code == 200

    notification = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'receipt_escalated',
        )
    ).scalars().one()
    assert notification.message == question
    assert notification.payload['question'] == question


def test_missing_phone_fails_soft_queued_failed_row(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-SMS7').status_code == 200
    resp = _decision(client, token, _queue_id(client, token, 'TXN-SMS7'), {'verdict': 'escalate', 'note': 'Question?'})
    assert resp.status_code == 200  # banner still fires

    rows = db_session.execute(select(SmsMessage)).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == 'failed'
    assert rows[0].error_message == 'no_phone_on_file'

    notification = db_session.execute(
        select(Notification).where(Notification.kind == 'receipt_escalated')
    ).scalars().one()
    assert notification.organization_id == org.id


def test_escalation_keeps_workspace_locked(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-SMS8').status_code == 200
    assert _decision(client, token, _queue_id(client, token, 'TXN-SMS8'), {'verdict': 'escalate', 'note': 'Question?'}).status_code == 200

    db_session.refresh(org)
    assert org.billing_phase == 'grace'


def test_escalated_receipt_back_in_queue_for_final_decision(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-SMS9').status_code == 200
    receipt_id = _queue_id(client, token, 'TXN-SMS9')
    assert _decision(client, token, receipt_id, {'verdict': 'escalate', 'note': 'Question?'}).status_code == 200

    queue = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    item = next(row for row in queue if row['id'] == receipt_id)
    assert item['status'] == 'escalated'

    # Admin renders a final verdict on the escalated receipt.
    assert _decision(client, token, receipt_id, {'verdict': 'verify'}).status_code == 200
    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == 0
    assert invoice.status == 'paid'
