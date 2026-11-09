from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dispute_thread import DisputeThread
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.sms_message import SmsMessage
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trusted_payer import TrustedPayer
from app.models.wallet_credit import WalletCredit


def _org(db: Session, name: str = 'Receipts Test Co') -> Organization:
    org = Organization(
        name=name,
        slug=f'receipts-test-{name.lower().replace(" ", "-")}',
        primary_email_domain='receiptstest.com',
        subscription_tier='starter',
        subscription_status='past_due',
        billing_phase='hard_locked',
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _invoice(db: Session, org: Organization, number: str) -> SubscriptionInvoice:
    from app.models.collection_account import CollectionAccount

    cbe = db.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'cbe')
    ).scalar_one()
    invoice = SubscriptionInvoice(
        organization_id=org.id,
        invoice_number=number,
        tier='starter',
        billing_period_start=date(2026, 8, 1),
        billing_period_end=date(2026, 8, 31),
        flat_amount_etb=Decimal('4500.00'),
        total_etb=Decimal('4520.00'),
        balance_remaining_etb=Decimal('4520.00'),
        due_date=date(2026, 8, 1),
        grace_days=3,
        grace_ends_at=date(2026, 8, 4),
        designated_account_id=cbe.id,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def _receipt(db: Session, org: Organization, invoice: SubscriptionInvoice | None, *, ref: str | None, status: str = 'pending') -> PaymentReceipt:
    receipt = PaymentReceipt(
        organization_id=org.id,
        invoice_id=invoice.id if invoice else None,
        file_name='receipt.png',
        content_type='image/png',
        file_size_bytes=64,
        file_data=b'\x89PNG\r\n\x1a\n' + b'0' * 64,
        file_sha256='a' * 64,
        reference_number=ref,
        amount_etb=Decimal('4520.00'),
        status=status,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def test_payment_receipt_status_check_constraint(db_session: Session):
    org = _org(db_session)
    db_session.add(
        PaymentReceipt(
            organization_id=org.id,
            file_name='receipt.png',
            content_type='image/png',
            file_size_bytes=64,
            file_data=b'\x89PNG\r\n\x1a\n' + b'0' * 64,
            file_sha256='a' * 64,
            status='bogus',
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_payment_receipt_verdict_check_constraint(db_session: Session):
    org = _org(db_session)
    invoice = _invoice(db_session, org, 'INV-900001')
    receipt = _receipt(db_session, org, invoice, ref='TXN-V1')
    receipt.verdict = 'amount_mismatch'
    db_session.add(receipt)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_verified_reference_partial_unique(db_session: Session):
    """Two VERIFIED receipts with the same ref -> IntegrityError;
    verified + pending coexist."""
    org_a = _org(db_session, 'Org A')
    org_b = _org(db_session, 'Org B')
    invoice_a = _invoice(db_session, org_a, 'INV-900002')
    invoice_b = _invoice(db_session, org_b, 'INV-900003')

    _receipt(db_session, org_a, invoice_a, ref='TXN-UNIQUE-1', status='verified')
    # Pending with the same ref is allowed (both visible in the queue).
    pending = _receipt(db_session, org_b, invoice_b, ref='TXN-UNIQUE-1', status='pending')
    assert pending.status == 'pending'

    # Second verified with the same ref is rejected by the partial index.
    second = _receipt(db_session, org_b, invoice_b, ref='TXN-UNIQUE-1', status='pending')
    second.status = 'verified'
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_wallet_credit_positive_amount_check(db_session: Session):
    org = _org(db_session)
    invoice = _invoice(db_session, org, 'INV-900004')
    receipt = _receipt(db_session, org, invoice, ref='TXN-WAL1')
    db_session.add(
        WalletCredit(
            organization_id=org.id,
            receipt_id=receipt.id,
            amount_etb=Decimal('0.00'),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_trusted_payer_org_sender_unique(db_session: Session):
    org = _org(db_session)
    db_session.add_all(
        [
            TrustedPayer(organization_id=org.id, sender_name='mulugeta tesfaye'),
            TrustedPayer(organization_id=org.id, sender_name='mulugeta tesfaye'),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_dispute_thread_one_per_receipt(db_session: Session):
    org = _org(db_session)
    invoice = _invoice(db_session, org, 'INV-900005')
    receipt = _receipt(db_session, org, invoice, ref='TXN-DSP1', status='rejected')
    db_session.add_all(
        [
            DisputeThread(organization_id=org.id, receipt_id=receipt.id, dispute_text='This was my payment'),
            DisputeThread(organization_id=org.id, receipt_id=receipt.id, dispute_text='Duplicate dispute'),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_sms_status_check_constraint(db_session: Session):
    org = _org(db_session)
    db_session.add(
        SmsMessage(
            organization_id=org.id,
            to_phone='+251911000000',
            body='Hi there',
            status='bogus',
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_org_contact_phone_column(db_session: Session):
    org = _org(db_session)
    org.contact_phone = '+251911123456'
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    assert org.contact_phone == '+251911123456'
