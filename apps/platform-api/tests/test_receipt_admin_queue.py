import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.payment_receipt import PaymentReceipt
from app.models.trusted_payer import TrustedPayer
from app.models.user import User
from app.schemas.receipts import Verdict
from app.services.billing.receipt_extraction import ZERO_CONFIDENCE_WARNING
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(
    client: TestClient,
    token: str,
    *,
    amount: str = '4520.00',
    ref: str,
    sender: str = 'Mulugeta Tesfaye',
    bank: str = 'cbe',
    with_key: bool = True,
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
            'bank_identifier': bank,
        }
    )
    return client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )


def _queue(client: TestClient, token: str):
    resp = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    return resp.json()


def _decision(client: TestClient, token: str, receipt_id: str, body: dict):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json=body,
    )


def _add_trusted(db_session: Session, org_id, sender: str, admin_id=None) -> None:
    db_session.add(TrustedPayer(organization_id=org_id, sender_name=sender.casefold(), added_by_user_id=admin_id))
    db_session.commit()


def test_queue_lists_pending_and_escalated_only(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-Q1').status_code == 200
    assert _upload(client, token, ref='TXN-Q2').status_code == 200
    # reject one -> must NOT appear in queue
    rows = _queue(client, token)
    rejected = rows[0]
    assert _decision(client, token, rejected['id'], {'verdict': 'reject_illegible'}).status_code == 200

    queue_ids = [item['id'] for item in _queue(client, token)]
    assert len(queue_ids) == 1
    assert rejected['id'] not in queue_ids


def test_queue_gate_denies_operator_and_viewer(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-G1').status_code == 200

    operator = db_session.execute(
        select(User).where(User.username == 'operator')
    ).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=org.id, user_id=operator.id, role='operator', is_active=True
        )
    )
    viewer = db_session.execute(
        select(User).where(User.username == 'viewer')
    ).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=org.id, user_id=viewer.id, role='viewer', is_active=True
        )
    )
    db_session.commit()

    op_token = client.post('/api/v1/auth/login', json={'username': 'operator', 'password': 'operator12345'}).json()['access_token']
    viewer_token = client.post('/api/v1/auth/login', json={'username': 'viewer', 'password': 'viewer12345'}).json()['access_token']

    assert client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {op_token}'}).status_code == 403
    assert client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {viewer_token}'}).status_code == 403


def test_queue_item_renders_flags(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='6000.00', ref='TXN-F1', bank='dashen').status_code == 200
    item = _queue(client, token)[0]
    for flag in (
        'is_new_sender',
        'is_cash_sender',
        'is_wrong_bank_within_portfolio',
        'is_large_surplus',
        'is_duplicate',
        'has_zero_confidence',
    ):
        assert flag in item
    assert item['is_new_sender'] is True
    assert item['is_large_surplus'] is True
    assert item['is_wrong_bank_within_portfolio'] is True
    assert item['surplus_etb'] == '1480.00'
    assert item['recommended_verdict'] == 'verify'


def test_new_sender_flag_when_not_trusted(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-NS1').status_code == 200
    item = _queue(client, token)[0]
    assert item['is_new_sender'] is True
    assert item['recommended_verdict'] is None


def test_trusted_payer_prefills_verify(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    _add_trusted(db_session, org.id, 'Mulugeta Tesfaye')
    assert _upload(client, token, ref='TXN-TP1').status_code == 200
    item = _queue(client, token)[0]
    assert item['is_new_sender'] is False
    assert item['recommended_verdict'] == 'verify'


def test_cash_sender_double_flagged_even_when_trusted_and_no_prefill(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    _add_trusted(db_session, org.id, 'CASH')
    assert _upload(client, token, ref='TXN-CS1', sender='CASH').status_code == 200
    item = _queue(client, token)[0]
    assert item['is_cash_sender'] is True
    assert item['is_new_sender'] is False
    assert item['recommended_verdict'] is None


def test_wrong_bank_within_portfolio_prefills_verify(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    # invoice designates CBE (helper) -> Dashen receipt is within portfolio
    assert _upload(client, token, ref='TXN-WB1', bank='dashen').status_code == 200
    item = _queue(client, token)[0]
    assert item['is_wrong_bank_within_portfolio'] is True
    assert item['designated_bank_code'] == 'cbe'
    assert item['recommended_verdict'] == 'verify'


def test_zero_confidence_warning_text(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice(with_ai_key=False)
    assert _upload(client, token, ref='TXN-ZC1').status_code == 200
    item = _queue(client, token)[0]
    assert item['has_zero_confidence'] is True
    assert item['zero_confidence_warning'] == ZERO_CONFIDENCE_WARNING


def test_low_confidence_visual_flags_present(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    payload = mock_extraction_payload(
        fields={
            'sender_name': 'Mulugeta Tesfaye',
            'sender_account_number': '1000123456',
            'receiver_account_number': '1000134567890',
            'receiver_name': 'FreightPilot PLC',
            'transfer_amount': '4520.00',
            'transfer_date': '2026-08-01',
            'reference_number': 'TXN-LC1',
            'bank_identifier': 'cbe',
        }
    )
    payload['confidence']['sender_name'] = 0.3
    resp = client.post(
        '/api/v1/receipts/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )
    assert resp.status_code == 200
    item = _queue(client, token)[0]
    assert 'sender_name' in item['low_confidence_fields']


def test_verify_add_trusted_payer_persists_and_audits(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-AD1').status_code == 200
    receipt_id = _queue(client, token)[0]['id']
    resp = _decision(
        client, token, receipt_id,
        {'verdict': 'verify', 'trusted_payer_action': 'added'},
    )
    assert resp.status_code == 200

    rows = db_session.execute(
        select(TrustedPayer).where(TrustedPayer.organization_id == org.id)
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].sender_name == 'mulugeta tesfaye'

    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.trusted_payer_action == 'added'

    events = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.trusted_payer_added')
    ).scalars().all()
    assert len(events) == 1
    assert events[0].payload['sender_name'] == 'mulugeta tesfaye'


def test_verify_do_not_add_leaves_list_unchanged(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-DN1').status_code == 200
    receipt_id = _queue(client, token)[0]['id']
    resp = _decision(
        client, token, receipt_id,
        {'verdict': 'verify', 'trusted_payer_action': 'verified_once'},
    )
    assert resp.status_code == 200

    rows = db_session.execute(
        select(TrustedPayer).where(TrustedPayer.organization_id == org.id)
    ).scalars().all()
    assert rows == []
    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.trusted_payer_action == 'verified_once'


def test_reject_wrong_bank_in_portfolio_422(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-RWB1', bank='cbe').status_code == 200
    receipt_id = _queue(client, token)[0]['id']
    resp = _decision(client, token, receipt_id, {'verdict': 'reject_wrong_bank'})
    assert resp.status_code == 422


def test_reject_wrong_bank_out_of_portfolio_allowed(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-RWB2', bank='awash').status_code == 200
    receipt_id = _queue(client, token)[0]['id']
    resp = _decision(client, token, receipt_id, {'verdict': 'reject_wrong_bank'})
    assert resp.status_code == 200
    receipt = db_session.get(PaymentReceipt, receipt_id)
    assert receipt.status == 'rejected'
    assert receipt.verdict == 'reject_wrong_bank'


def test_escalate_requires_note_422(
    client: TestClient, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, ref='TXN-ESC0').status_code == 200
    receipt_id = _queue(client, token)[0]['id']
    resp = _decision(client, token, receipt_id, {'verdict': 'escalate'})
    assert resp.status_code == 422


def test_verdict_enum_has_no_amount_mismatch():
    values = [verdict.value for verdict in Verdict]
    assert len(values) == 5
    assert 'amount_mismatch' not in values
    assert values == ['verify', 'reject_wrong_bank', 'reject_duplicate', 'reject_illegible', 'escalate']
