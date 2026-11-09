"""Fraud-risk badge (TECH-21 / NB-21, decision #6).

The badge lives in ``sender_fraud_flags`` (NOT on trusted_payers), fires
on undo AND reverse when the ORIGINAL verified audit payload shows
``trusted_payer_action == 'added'``, surfaces on EVERY future queue item
for that sender, survives trusted-payer list removal, and NEVER hard-blocks
verification (NB-21.4 / NB-21.6).
"""

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.sender_fraud_flag import SenderFraudFlag
from app.models.trusted_payer import TrustedPayer
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _undo(client: TestClient, token: str, receipt_id: str):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/undo',
        headers={'Authorization': f'Bearer {token}'},
        json={},
    )


def _reverse(client: TestClient, token: str, receipt_id: str, reason: str = 'Fraud investigation'):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/reverse',
        headers={'Authorization': f'Bearer {token}'},
        json={'reason': reason},
    )


def _queue(client: TestClient, token: str):
    resp = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    return resp.json()


def _upload(client: TestClient, token: str, *, ref: str, sender: str = 'Mulugeta Tesfaye'):
    payload = mock_extraction_payload(
        fields={
            'sender_name': sender,
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


def _flags(db: Session, org_id) -> list[SenderFraudFlag]:
    return db.execute(
        select(SenderFraudFlag).where(SenderFraudFlag.organization_id == org_id)
    ).scalars().all()


def test_reverse_of_verify_added_flags_sender(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F1', trusted_payer_action='added')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()

    resp = _reverse(client, token, receipt_id, reason='Fraud investigation')
    assert resp.status_code == 200

    flags = _flags(db_session, org.id)
    assert len(flags) == 1
    assert flags[0].sender_name == 'mulugeta tesfaye'
    assert flags[0].reversal_count == 1
    assert flags[0].fraud_risk_since is not None

    audited = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.fraud_flagged',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().all()
    assert len(audited) == 1
    assert audited[0].payload['sender_name'] == 'mulugeta tesfaye'


def test_undo_of_verify_added_also_flags_sender(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    """Decision #6: a silent clawback is the stronger fraud signal — the
    badge fires on BOTH mechanisms."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F2', trusted_payer_action='added')

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    flags = _flags(db_session, org.id)
    assert len(flags) == 1
    assert flags[0].sender_name == 'mulugeta tesfaye'


def test_verify_without_added_never_flags(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F3', trusted_payer_action='verified_once')
    assert _undo(client, token, receipt_id).status_code == 200

    assert _flags(db_session, org.id) == []
    assert db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.fraud_flagged')
    ).scalars().all() == []


def test_badge_surfaces_on_future_queue_item(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F4', trusted_payer_action='added')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()
    assert _reverse(client, token, receipt_id, reason='Fraud investigation').status_code == 200

    # Every future queue item for that sender carries the badge.
    assert _upload(client, token, ref='TXN-F5', sender='Mulugeta Tesfaye').status_code == 200
    item = next(i for i in _queue(client, token) if i['extracted_fields']['reference_number'] == 'TXN-F5')
    assert item['sender_has_reversed_credit'] is True
    assert item['fraud_risk_since'] is not None


def test_badge_persists_across_uploads_and_orgs(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org_a, invoice, token_a = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token_a, 'TXN-F6', trusted_payer_action='added')
    assert _undo(client, token_a, receipt_id).status_code == 200
    assert len(_flags(db_session, org_a.id)) == 1

    # Another org's identical sender is unflagged (flag is per-org).
    org_b, invoice_b, token_b = make_paid_org_with_open_invoice(invoice_number='INV-000200')
    assert _upload(client, token_b, ref='TXN-F7', sender='Mulugeta Tesfaye').status_code == 200
    item = next(i for i in _queue(client, token_b) if i['extracted_fields']['reference_number'] == 'TXN-F7')
    assert item['sender_has_reversed_credit'] is False
    assert item['fraud_risk_since'] is None
    assert _flags(db_session, org_b.id) == []


def test_badge_does_not_block_verification(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    """NB-21.4: the badge is display-only — verify still succeeds."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F8', trusted_payer_action='added')
    assert _undo(client, token, receipt_id).status_code == 200

    assert _upload(client, token, ref='TXN-F9', sender='Mulugeta Tesfaye').status_code == 200
    rows = _queue(client, token)
    new_id = next(i['id'] for i in rows if i['extracted_fields']['reference_number'] == 'TXN-F9')
    assert next(i['sender_has_reversed_credit'] for i in rows if i['id'] == new_id) is True

    resp = client.post(
        f'/api/v1/receipts/{new_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json={'verdict': 'verify', 'trusted_payer_action': 'verified_once'},
    )
    assert resp.status_code == 200


def test_badge_survives_trusted_payer_removal(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    """NB-21.3/21.5: list removal does NOT clear the flag."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F10', trusted_payer_action='added')
    assert _undo(client, token, receipt_id).status_code == 200

    resp = client.delete(
        f"/api/v1/receipts/trusted-payers/{'Mulugeta%20Tesfaye'}",
        headers={'Authorization': f'Bearer {token}'},
        params={'organization_id': str(org.id)},
    )
    assert resp.status_code == 200
    assert resp.json() == {'removed': True}
    assert db_session.execute(select(TrustedPayer)).scalars().all() == []

    # Badge still surfaces on the next receipt from that sender.
    assert _upload(client, token, ref='TXN-F11', sender='Mulugeta Tesfaye').status_code == 200
    item = next(i for i in _queue(client, token) if i['extracted_fields']['reference_number'] == 'TXN-F11')
    assert item['sender_has_reversed_credit'] is True
    assert item['fraud_risk_since'] is not None


def test_remove_trusted_payer_endpoint_audits_and_404s_unknown(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    org, invoice, token = make_paid_org_with_open_invoice()
    verify_receipt(token, 'TXN-F12', trusted_payer_action='added')

    resp = client.delete(
        '/api/v1/receipts/trusted-payers/Unknown%20Sender',
        headers={'Authorization': f'Bearer {token}'},
        params={'organization_id': str(org.id)},
    )
    assert resp.status_code == 404

    resp = client.delete(
        '/api/v1/receipts/trusted-payers/Mulugeta%20Tesfaye',
        headers={'Authorization': f'Bearer {token}'},
        params={'organization_id': str(org.id)},
    )
    assert resp.status_code == 200
    assert resp.json() == {'removed': True}
    events = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'receipts.trusted_payer_removed')
    ).scalars().all()
    assert len(events) == 1
    assert events[0].payload['sender_name'] == 'mulugeta tesfaye'


def test_single_reversal_never_hard_blocks(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, verify_receipt
):
    """NB-21.6: one reversal never hard-blocks — no status change, no gating."""
    org, invoice, token = make_paid_org_with_open_invoice()
    receipt_id, _ = verify_receipt(token, 'TXN-F13', trusted_payer_action='added')
    assert _undo(client, token, receipt_id).status_code == 200

    assert _upload(client, token, ref='TXN-F14', sender='Mulugeta Tesfaye').status_code == 200
    item = next(i for i in _queue(client, token) if i['extracted_fields']['reference_number'] == 'TXN-F14')
    assert item['status'] == 'pending'
    assert item['sender_has_reversed_credit'] is True
    # recommended verdict unaffected by the badge (sender is still trusted)
    assert item['recommended_verdict'] == 'verify'
