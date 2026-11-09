from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice_line_item import InvoiceLineItem
from app.models.notification import Notification
from app.models.payment_receipt import PaymentReceipt
from app.models.wallet_credit import WalletCredit
from app.services.billing import invoices as invoices_service
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, amount: str, ref: str, sender: str = 'Mulugeta Tesfaye', bank: str = 'cbe'):
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
        data={'mock_extraction': __import__('json').dumps(payload)},
    )


def _verify(client: TestClient, token: str, receipt_id: str, **payload) -> object:
    body = {'verdict': 'verify', **payload}
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json=body,
    )


def _receipt_id(client: TestClient, token: str) -> str:
    rows = client.get('/api/v1/receipts', headers={'Authorization': f'Bearer {token}'}).json()
    return rows[0]['id']


def test_partial_credit_reduces_balance_invoice_stays_open(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='2000.00', ref='TXN-P1').status_code == 200
    resp = _verify(client, token, _receipt_id(client, token))
    assert resp.status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('2520.00')
    assert invoice.status == 'issued'


def test_exact_credit_marks_invoice_paid(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-E1').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('0.00')
    assert invoice.status == 'paid'


def test_small_surplus_credits_balance_and_creates_wallet_credit(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='5000.00', ref='TXN-S1').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('0.00')
    assert invoice.status == 'paid'

    wallet_rows = db_session.execute(
        select(WalletCredit).where(WalletCredit.organization_id == org.id)
    ).scalars().all()
    assert len(wallet_rows) == 1
    assert wallet_rows[0].amount_etb == Decimal('480.00')
    assert wallet_rows[0].status == 'available'


def test_small_surplus_wallet_notification_copy(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='5000.00', ref='TXN-S2').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    notifications = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'wallet_credit',
        )
    ).scalars().all()
    assert len(notifications) == 1
    assert notifications[0].message == 'Wallet balance: +480.00 ETB applies to next invoice.'


def test_large_surplus_requires_admin_decision_422_without(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    # 6000 > 4520 + 1000
    assert _upload(client, token, amount='6000.00', ref='TXN-L1').status_code == 200
    resp = _verify(client, token, _receipt_id(client, token))
    assert resp.status_code == 422
    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('4520.00')
    assert invoice.status == 'issued'


def test_large_surplus_credit_forward_closes_invoice_and_wallets(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='6000.00', ref='TXN-L2').status_code == 200
    assert _verify(client, token, _receipt_id(client, token), large_surplus_decision='credit_forward').status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('0.00')
    assert invoice.status == 'paid'
    wallet_rows = db_session.execute(
        select(WalletCredit).where(WalletCredit.organization_id == org.id)
    ).scalars().all()
    assert len(wallet_rows) == 1
    assert wallet_rows[0].amount_etb == Decimal('1480.00')


def test_large_surplus_credit_backward_audits_no_wallet(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='6000.00', ref='TXN-L3').status_code == 200
    assert _verify(client, token, _receipt_id(client, token), large_surplus_decision='credit_backward').status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('0.00')
    wallet_rows = db_session.execute(
        select(WalletCredit).where(WalletCredit.organization_id == org.id)
    ).scalars().all()
    assert wallet_rows == []

    from app.models.audit_event import AuditEvent

    event = db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.verified',
            AuditEvent.organization_id == org.id,
        )
    ).scalars().one()
    assert event.payload['large_surplus_decision'] == 'credit_backward'
    assert event.payload['surplus_etb'] == '1480.00'


def test_large_surplus_partial_ignore_keeps_balance_open_when_under(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='6000.00', ref='TXN-L4').status_code == 200
    resp = _verify(
        client, token, _receipt_id(client, token),
        large_surplus_decision='partial_ignore',
        partial_credit_amount_etb='1000.00',
    )
    assert resp.status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('3520.00')
    assert invoice.status == 'issued'
    wallet_rows = db_session.execute(
        select(WalletCredit).where(WalletCredit.organization_id == org.id)
    ).scalars().all()
    assert wallet_rows == []


def test_verify_unlocks_workspace_via_refresh(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-U1').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    db_session.refresh(org)
    assert org.billing_phase == 'active'


def test_partial_verify_keeps_workspace_locked(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='1000.00', ref='TXN-U2').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    db_session.refresh(org)
    assert org.billing_phase == 'grace'


def test_wallet_credit_applied_to_next_invoice_at_issuance(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    # surplus = 4770 - 4520 = 250 -> wallet credit
    assert _upload(client, token, amount='4770.00', ref='TXN-W1').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    next_invoice = invoices_service.issue_next_invoice(db_session, org, datetime.now(UTC))
    assert next_invoice.total_etb == Decimal('4250.00')
    assert next_invoice.balance_remaining_etb == Decimal('4250.00')
    assert next_invoice.flat_amount_etb == Decimal('4500.00')

    wallet_lines = db_session.execute(
        select(InvoiceLineItem).where(
            InvoiceLineItem.invoice_id == next_invoice.id,
            InvoiceLineItem.kind == 'wallet_credit',
        )
    ).scalars().all()
    assert len(wallet_lines) == 1
    assert wallet_lines[0].amount_etb == Decimal('-250.00')

    wallet_rows = db_session.execute(
        select(WalletCredit).where(
            WalletCredit.organization_id == org.id,
            WalletCredit.status == 'applied',
        )
    ).scalars().all()
    assert len(wallet_rows) == 1
    assert wallet_rows[0].applied_to_invoice_id == next_invoice.id
    assert wallet_rows[0].applied_at is not None


def test_wallet_credit_exceeding_next_total_rolls_remainder(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):

    org, invoice, token = make_paid_org_with_open_invoice()
    # Backing receipt row (wallet_credits.receipt_id is NOT NULL).
    backing = PaymentReceipt(
        organization_id=org.id,
        invoice_id=invoice.id,
        file_name='receipt.png',
        content_type='image/png',
        file_size_bytes=64,
        file_data=b'\x89PNG\r\n\x1a\n' + b'0' * 64,
        file_sha256='b' * 64,
        reference_number='TXN-WB1',
        amount_etb=Decimal('6000.00'),
        status='verified',
    )
    db_session.add(backing)
    db_session.flush()
    db_session.add(
        WalletCredit(
            organization_id=org.id,
            receipt_id=backing.id,
            amount_etb=Decimal('6000.00'),
            status='available',
        )
    )
    db_session.commit()

    next_invoice = invoices_service.issue_next_invoice(db_session, org, datetime.now(UTC))
    assert next_invoice.total_etb == Decimal('0.00')
    assert next_invoice.balance_remaining_etb == Decimal('0.00')

    remainder = db_session.execute(
        select(WalletCredit.amount_etb).where(
            WalletCredit.organization_id == org.id,
            WalletCredit.status == 'available',
        )
    ).scalars().all()
    assert sum(remainder, Decimal('0.00')) == Decimal('1500.00')


def test_credit_amount_never_rejection_reason(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    """NB-08.6 / NB-15.3: partial of any size verifies — no rejection."""
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='1.00', ref='TXN-T1').status_code == 200
    assert _verify(client, token, _receipt_id(client, token)).status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('4519.00')
