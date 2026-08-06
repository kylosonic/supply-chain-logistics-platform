from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord
from app.models.usage_meter import OrganizationUsageCounter
from app.services.billing import invoices


def _org(db: Session, *, tier: str = 'starter', name: str = 'Invoice Co') -> Organization:
    org = Organization(
        name=name,
        slug=name.lower().replace(' ', '-'),
        primary_email_domain='invoiceco.com',
        subscription_tier=tier,
        subscription_status='trialing',
        billing_phase='limbo',
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _ended_trial(
    db: Session,
    org: Organization,
    tier: str,
    *,
    started: datetime,
    ended: datetime,
) -> None:
    org.subscription_tier = tier
    org.trial_started_at = started
    org.trial_ends_at = ended
    db.add(
        TrialRecord(organization_id=org.id, tier=tier, started_at=started, ended_at=ended)
    )
    db.commit()


def _counter(db: Session, org: Organization, metric: str, used: int, period: tuple[date, date]) -> None:
    db.add(
        OrganizationUsageCounter(
            organization_id=org.id,
            metric=metric,
            period_start=period[0],
            period_end=period[1],
            used_units=used,
        )
    )
    db.commit()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def test_first_invoice_starter_line_items(db_session: Session):
    org = _org(db_session, tier='starter')
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    _counter(db_session, org, 'delivery_tasks', 2600, (date(2026, 7, 1), date(2026, 7, 31)))

    invoice = invoices.issue_first_invoice(db_session, org, datetime(2026, 8, 1, tzinfo=UTC))
    db_session.commit()

    assert invoice.flat_amount_etb == Decimal('4500.00')
    assert invoice.billing_period_start == date(2026, 8, 1)
    assert invoice.billing_period_end == date(2026, 8, 31)
    lines = {line.kind: line for line in invoice.lines}
    assert lines['flat'].amount_etb == Decimal('4500.00')
    overage = lines['overage_delivery_tasks']
    assert overage.quantity == 100
    assert overage.unit_price_etb == Decimal('0.20')
    assert overage.amount_etb == Decimal('20.00')
    assert 'overage_route_optimizations' not in lines
    assert invoice.total_etb == Decimal('4520.00')
    assert invoice.balance_remaining_etb == Decimal('4520.00')


def test_first_invoice_scale_quarterly_period(db_session: Session):
    org = _org(db_session, tier='scale')
    _ended_trial(
        db_session,
        org,
        'scale',
        started=datetime(2026, 8, 8, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
    )

    invoice = invoices.issue_first_invoice(db_session, org, datetime(2026, 10, 1, tzinfo=UTC))

    assert invoice.billing_period_start == date(2026, 10, 1)
    assert invoice.billing_period_end == date(2026, 12, 31)
    assert invoice.flat_amount_etb == Decimal('10000.00')
    assert invoice.total_etb == Decimal('10000.00')


def test_enterprise_invoice_never_has_overage_lines(db_session: Session):
    org = _org(db_session, tier='enterprise')
    _ended_trial(
        db_session,
        org,
        'enterprise',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    _counter(db_session, org, 'delivery_tasks', 999999, (date(2026, 7, 1), date(2026, 7, 31)))
    _counter(db_session, org, 'route_optimizations', 999999, (date(2026, 7, 1), date(2026, 7, 31)))

    invoice = invoices.issue_first_invoice(db_session, org, datetime(2026, 8, 1, tzinfo=UTC))
    db_session.commit()

    kinds = [line.kind for line in invoice.lines]
    assert kinds == ['flat']
    assert invoice.flat_amount_etb == Decimal('45000.00')
    assert invoice.total_etb == Decimal('45000.00')


def test_invoice_designates_exactly_one_account(db_session: Session):
    org = _org(db_session)
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )

    invoice = invoices.issue_first_invoice(db_session, org, datetime(2026, 8, 1, tzinfo=UTC))

    assert invoice.designated_account_id is not None
    assert invoice.designated_account.bank_code in {'cbe', 'dashen'}
    assert invoice.designated_account.account_holder
    assert invoice.designated_account.account_number


def test_designation_rotates_per_org(db_session: Session):
    org = _org(db_session)
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )

    first = invoices.issue_first_invoice(db_session, org, datetime(2026, 8, 1, tzinfo=UTC))
    db_session.commit()
    second = invoices.issue_next_invoice(db_session, org, datetime(2026, 9, 1, tzinfo=UTC))
    db_session.commit()

    assert first.designated_account.bank_code == 'cbe'
    assert second.designated_account.bank_code == 'dashen'
    assert second.billing_period_start == date(2026, 9, 1)


def test_invoice_number_format_and_uniqueness(db_session: Session):
    org_a = _org(db_session, name='Invoice Co A')
    org_b = _org(db_session, name='Invoice Co B')
    _ended_trial(
        db_session, org_a, 'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    _ended_trial(
        db_session, org_b, 'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )

    inv_a = invoices.issue_first_invoice(db_session, org_a, datetime(2026, 8, 1, tzinfo=UTC))
    inv_b = invoices.issue_first_invoice(db_session, org_b, datetime(2026, 8, 1, tzinfo=UTC))

    assert inv_a.invoice_number == 'INV-000001'
    assert inv_b.invoice_number == 'INV-000002'


def test_at_most_one_invoice_per_period(db_session: Session):
    org = _org(db_session)
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )

    now = datetime(2026, 8, 1, tzinfo=UTC)
    first = invoices.try_issue_invoice(db_session, org, now)
    second = invoices.try_issue_invoice(db_session, org, now)

    assert first is not None
    assert second is not None
    assert first.id == second.id
    rows = db_session.execute(
        select(SubscriptionInvoice).where(SubscriptionInvoice.organization_id == org.id)
    ).scalars().all()
    assert len(rows) == 1


def test_first_invoice_grace_3_subsequent_0(db_session: Session):
    org = _org(db_session)
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )

    first = invoices.issue_first_invoice(db_session, org, datetime(2026, 8, 1, tzinfo=UTC))
    db_session.commit()
    second = invoices.issue_next_invoice(db_session, org, datetime(2026, 9, 1, tzinfo=UTC))
    db_session.commit()

    assert first.grace_days == 3
    assert first.grace_ends_at == date(2026, 8, 4)
    assert second.grace_days == 0
    assert second.grace_ends_at == second.due_date


def test_warning_notification_fields(db_session: Session):
    org = _org(db_session)
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    _counter(db_session, org, 'delivery_tasks', 2600, (date(2026, 7, 1), date(2026, 7, 31)))
    now = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)

    invoices.issue_first_invoice(db_session, org, now)
    db_session.commit()
    notification = db_session.execute(
        select(Notification).where(Notification.organization_id == org.id)
    ).scalars().one()

    assert notification.kind == 'invoice_warning'
    payload = notification.payload
    assert payload['invoice_number'] == 'INV-000001'
    assert payload['amount_etb'] == '4520.00'
    assert payload['flat_amount_etb'] == '4500.00'
    assert payload['bank_name']
    assert payload['bank_code'] == 'cbe'
    assert payload['bank_account']
    assert payload['due_date'] == '2026-08-01'
    assert payload['grace_ends_at'] == '2026-08-04'
    assert _utc(notification.expires_at) == now + timedelta(days=3)


def test_issue_records_audit_event(db_session: Session):
    org = _org(db_session)
    _ended_trial(
        db_session,
        org,
        'starter',
        started=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        ended=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )

    invoices.issue_first_invoice(db_session, org, datetime(2026, 8, 1, tzinfo=UTC))
    db_session.commit()

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'billing.invoice_issued')
    ).scalars().one()
    assert event.organization_id == org.id
    assert event.payload['invoice_number'] == 'INV-000001'
    assert event.payload['designated_account'] == 'cbe'
