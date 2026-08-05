from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.billing_counter import BillingCounter
from app.models.collection_account import CollectionAccount
from app.models.invoice_line_item import InvoiceLineItem
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord


def _org(db: Session, name: str = 'Billing Test Co') -> Organization:
    org = Organization(
        name=name,
        slug=f'billing-test-{name.lower().replace(" ", "-")}',
        primary_email_domain='billingtest.com',
        subscription_tier='free',
        subscription_status='active',
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def test_collection_accounts_check_constraint_rejects_unknown_bank(db_session: Session):
    db_session.add(
        CollectionAccount(
            bank_code='awash',
            bank_name='Awash Bank',
            account_holder='FreightPilot PLC',
            account_number='1234567890',
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_subscription_invoice_org_period_unique(db_session: Session):
    org = _org(db_session)
    cbe = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'cbe')
    ).scalar_one()

    db_session.add_all(
        [
            SubscriptionInvoice(
                organization_id=org.id,
                invoice_number='INV-000001',
                tier='starter',
                billing_period_start=date(2026, 8, 1),
                billing_period_end=date(2026, 8, 31),
                flat_amount_etb=4500,
                total_etb=4500,
                balance_remaining_etb=4500,
                due_date=date(2026, 8, 1),
                grace_days=3,
                grace_ends_at=date(2026, 8, 4),
                designated_account_id=cbe.id,
            ),
            SubscriptionInvoice(
                organization_id=org.id,
                invoice_number='INV-000002',
                tier='starter',
                billing_period_start=date(2026, 8, 1),
                billing_period_end=date(2026, 8, 31),
                flat_amount_etb=4500,
                total_etb=4500,
                balance_remaining_etb=4500,
                due_date=date(2026, 8, 1),
                grace_days=3,
                grace_ends_at=date(2026, 8, 4),
                designated_account_id=cbe.id,
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_trial_record_org_tier_unique(db_session: Session):
    org = _org(db_session)
    now = datetime.now(UTC)
    db_session.add_all(
        [
            TrialRecord(organization_id=org.id, tier='starter', started_at=now),
            TrialRecord(organization_id=org.id, tier='starter', started_at=now),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_seed_collection_accounts_present(db_session: Session):
    accounts = db_session.execute(select(CollectionAccount).order_by(CollectionAccount.bank_code)).scalars().all()
    assert [a.bank_code for a in accounts] == ['cbe', 'dashen']
    assert all(a.is_active for a in accounts)
    assert all(a.account_holder and a.account_number for a in accounts)
