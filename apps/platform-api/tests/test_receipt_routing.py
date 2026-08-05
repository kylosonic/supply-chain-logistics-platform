import datetime as _dt
import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection_account import CollectionAccount
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.services.billing import credits
from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, amount: str, ref: str, sender: str = 'Mulugeta Tesfaye'):
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


def _verify(client: TestClient, token: str, receipt_id: str, **payload):
    return client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers={'Authorization': f'Bearer {token}'},
        json={'verdict': 'verify', **payload},
    )


def _newest_receipt(client: TestClient, token: str) -> str:
    rows = client.get('/api/v1/receipts', headers={'Authorization': f'Bearer {token}'}).json()
    pending = [row for row in rows if row['status'] == 'pending']
    assert pending, 'no pending receipt to verify'
    return pending[0]['id']


def test_surplus_cascade_computes_secondary_targets(
    db_session: Session, make_paid_org_with_open_invoice
):
    """NB-07.3 unit-level: credited excess flows to next-oldest open invoices
    with the tolerance rules applied recursively."""
    org, invoice_a, token = make_paid_org_with_open_invoice(period_start=_dt.date(2026, 6, 1))
    account = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'dashen')
    ).scalar_one()
    today = _dt.date.today()
    invoice_b = SubscriptionInvoice(
        organization_id=org.id,
        invoice_number='INV-CAS-B',
        tier='starter',
        billing_period_start=_dt.date(2026, 7, 1),
        billing_period_end=_dt.date(2026, 7, 31),
        flat_amount_etb=Decimal('3000.00'),
        total_etb=Decimal('3000.00'),
        balance_remaining_etb=Decimal('3000.00'),
        due_date=_dt.date(2026, 7, 1),
        grace_days=0,
        grace_ends_at=today,
        designated_account_id=account.id,
        status='issued',
    )
    invoice_c = SubscriptionInvoice(
        organization_id=org.id,
        invoice_number='INV-CAS-C',
        tier='starter',
        billing_period_start=_dt.date(2026, 8, 1),
        billing_period_end=_dt.date(2026, 8, 31),
        flat_amount_etb=Decimal('5000.00'),
        total_etb=Decimal('5000.00'),
        balance_remaining_etb=Decimal('5000.00'),
        due_date=_dt.date(2026, 8, 1),
        grace_days=0,
        grace_ends_at=today,
        designated_account_id=account.id,
        status='issued',
    )
    db_session.add_all([invoice_b, invoice_c])
    db_session.commit()

    # 2500 excess: partial against INV-B (3000 balance) -> 500 left open.
    leftover = credits._cascade_surplus(db_session, org, Decimal('2500.00'), invoice_a)
    db_session.flush()
    assert leftover == Decimal('0.00')
    db_session.refresh(invoice_b)
    db_session.refresh(invoice_c)
    assert invoice_b.balance_remaining_etb == Decimal('500.00')
    assert invoice_c.balance_remaining_etb == Decimal('5000.00')

    # 5500 more: closes INV-B (500) then exact-matches INV-C (5000).
    leftover = credits._cascade_surplus(db_session, org, Decimal('5500.00'), invoice_a)
    db_session.flush()
    assert leftover == Decimal('0.00')
    db_session.refresh(invoice_b)
    db_session.refresh(invoice_c)
    assert invoice_b.balance_remaining_etb == Decimal('0.00')
    assert invoice_b.status == 'paid'
    assert invoice_c.balance_remaining_etb == Decimal('0.00')
    assert invoice_c.status == 'paid'

    # 9500 against paid invoices: nothing to absorb -> full remainder.
    leftover = credits._cascade_surplus(db_session, org, Decimal('9500.00'), invoice_a)
    db_session.flush()
    assert leftover == Decimal('9500.00')


def test_multiple_receipts_per_invoice_accumulate(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='1000.00', ref='TXN-M1').status_code == 200
    assert _verify(client, token, _newest_receipt(client, token)).status_code == 200
    assert _upload(client, token, amount='1500.00', ref='TXN-M2').status_code == 200
    assert _verify(client, token, _newest_receipt(client, token)).status_code == 200

    db_session.refresh(invoice)
    assert invoice.balance_remaining_etb == Decimal('2020.00')
    assert invoice.status == 'issued'

    receipts = db_session.execute(
        select(PaymentReceipt).where(PaymentReceipt.organization_id == org.id)
    ).scalars().all()
    assert len(receipts) == 2
    assert all(r.invoice_id == invoice.id for r in receipts)


def test_partial_receipt_never_routed_away(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    """Routing keys off invoice balance, never the receipt amount."""
    org, invoice_old, token = make_paid_org_with_open_invoice(period_start=_dt.date(2026, 6, 1))
    account = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'dashen')
    ).scalar_one()
    today = _dt.date.today()
    invoice_new = SubscriptionInvoice(
        organization_id=org.id,
        invoice_number='INV-NEW-2',
        tier='starter',
        billing_period_start=_dt.date(2026, 8, 1),
        billing_period_end=_dt.date(2026, 8, 31),
        flat_amount_etb=Decimal('4500.00'),
        total_etb=Decimal('4500.00'),
        balance_remaining_etb=Decimal('100.00'),
        due_date=_dt.date(2026, 8, 1),
        grace_days=0,
        grace_ends_at=today,
        designated_account_id=account.id,
        status='issued',
    )
    db_session.add(invoice_new)
    db_session.commit()

    assert _upload(client, token, amount='50.00', ref='TXN-PR1').status_code == 200
    receipt = db_session.execute(
        select(PaymentReceipt).where(PaymentReceipt.reference_number == 'TXN-PR1')
    ).scalars().one()
    # Routes to the OLDEST open invoice, not the one with the tiny balance.
    assert receipt.invoice_id == invoice_old.id


def test_duplicate_upload_skips_routing_and_queue(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice
):
    org, invoice, token = make_paid_org_with_open_invoice()
    assert _upload(client, token, amount='4520.00', ref='TXN-DUP1').status_code == 200
    assert _verify(client, token, _newest_receipt(client, token)).status_code == 200

    # Same reference again -> hard reject at upload.
    assert _upload(client, token, amount='4520.00', ref='TXN-DUP1').status_code == 200
    dup = db_session.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.reference_number == 'TXN-DUP1',
            PaymentReceipt.status == 'rejected',
        )
    ).scalars().one()
    assert dup.verdict == 'reject_duplicate'
    assert dup.invoice_id is None
    assert dup.is_duplicate is True

    queue = client.get('/api/v1/receipts/queue', headers={'Authorization': f'Bearer {token}'}).json()
    assert all(item['id'] != str(dup.id) for item in queue)
