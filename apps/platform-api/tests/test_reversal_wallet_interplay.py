"""Wallet interplay (decision #5): void un-applied, never claw back applied.

On undo/reverse every AVAILABLE WalletCredit row for the receipt flips to
``voided`` (+ ``voided_at``); the available pool recomputes to zero and the
customer wallet list surfaces the voided rows. Rows already ``applied`` to
a later invoice are LEFT UNTOUCHED — unwinding a consumed credit would
mutate a different invoice than the reversed one (NB-20.5).
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.payment_receipt import PaymentReceipt
from app.models.wallet_credit import WalletCredit
from app.services.billing import invoices as invoices_service
from app.services.billing.wallet import available_wallet_credit


def _undo(client: TestClient, token: str, receipt_id: str):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/undo',
        headers={'Authorization': f'Bearer {token}'},
        json={},
    )


def _reverse(client: TestClient, token: str, receipt_id: str, reason: str = 'Duplicate payment'):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/reverse',
        headers={'Authorization': f'Bearer {token}'},
        json={'reason': reason},
    )


def test_undo_voids_available_wallet_credit(
    client: TestClient, db_session: Session, make_verified_with_surplus
):
    org, invoice, token, receipt_id = make_verified_with_surplus(ref='TXN-WU1')
    assert available_wallet_credit(db_session, org) == Decimal('480.00')

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    row = db_session.execute(
        select(WalletCredit).where(WalletCredit.receipt_id == receipt_id)
    ).scalars().one()
    assert row.status == 'voided'
    assert row.voided_at is not None
    assert available_wallet_credit(db_session, org) == Decimal('0.00')

    event = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'wallet.voided',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().one()
    assert event.payload['amount_etb'] == '480.00'
    assert event.payload['reversal_kind'] == 'undo'
    assert event.payload['receipt_id'] == str(receipt_id)


def test_undo_does_not_claw_back_applied_wallet_credit(
    client: TestClient, db_session: Session, make_verified_with_surplus
):
    org, invoice, token, receipt_id = make_verified_with_surplus(ref='TXN-WU2')
    # The surplus (480 ETB) applies FIFO to the next invoice -> row becomes
    # 'applied' and the next invoice totals 4500 - 480 = 4020.
    next_invoice = invoices_service.issue_next_invoice(db_session, org, datetime.now(UTC))
    assert next_invoice.balance_remaining_etb == Decimal('4020.00')
    row = db_session.execute(
        select(WalletCredit).where(WalletCredit.receipt_id == receipt_id)
    ).scalars().one()
    assert row.status == 'applied'

    resp = _undo(client, token, receipt_id)
    assert resp.status_code == 200

    db_session.refresh(row)
    assert row.status == 'applied'  # untouched
    assert row.voided_at is None
    db_session.refresh(next_invoice)
    assert next_invoice.balance_remaining_etb == Decimal('4020.00')  # later invoice unchanged
    # No wallet.voided audit — nothing was voided.
    events = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'wallet.voided')
    ).scalars().all()
    assert events == []


def test_reverse_voids_available_wallet_credit(
    client: TestClient, db_session: Session, make_verified_with_surplus
):
    org, invoice, token, receipt_id = make_verified_with_surplus(ref='TXN-WR1')
    receipt = db_session.get(PaymentReceipt, receipt_id)
    receipt.decided_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.commit()

    resp = _reverse(client, token, receipt_id, reason='Bank reversal')
    assert resp.status_code == 200
    assert resp.json()['wallet_voided_etb'] == '480.00'

    row = db_session.execute(
        select(WalletCredit).where(WalletCredit.receipt_id == receipt_id)
    ).scalars().one()
    assert row.status == 'voided'
    assert row.voided_at is not None
    assert available_wallet_credit(db_session, org) == Decimal('0.00')

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'wallet.voided')
    ).scalars().one()
    assert event.payload['reversal_kind'] == 'reversed'


def test_wallet_list_surfaces_voided_rows(
    client: TestClient, db_session: Session, make_verified_with_surplus
):
    org, invoice, token, receipt_id = make_verified_with_surplus(ref='TXN-WL1')
    assert _undo(client, token, receipt_id).status_code == 200

    resp = client.get('/api/v1/receipts/wallet', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    body = resp.json()
    assert body['available_etb'] == '0.00'
    credits = [c for c in body['credits'] if c['status'] == 'voided']
    assert len(credits) == 1
    assert credits[0]['amount_etb'] == '480.00'
