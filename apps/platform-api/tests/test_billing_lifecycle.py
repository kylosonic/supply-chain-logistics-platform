from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord
from app.schemas.billing import WorkspacePhase
from app.services.billing import lifecycle
from app.services.billing.invoices import list_invoices


def _org(db: Session, *, tier: str = 'free') -> Organization:
    org = Organization(
        name='Lifecycle Co',
        slug='lifecycle-co',
        primary_email_domain='lifecycleco.com',
        subscription_tier=tier,
        subscription_status='active' if tier == 'free' else 'trialing',
        billing_phase='free',
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _start_trial(db: Session, org: Organization, tier: str, started: datetime) -> None:
    org.subscription_tier = tier
    org.subscription_status = 'trialing'
    org.billing_phase = WorkspacePhase.TRIAL.value
    org.trial_started_at = started
    org.trial_ends_at = started + timedelta(hours=168)
    db.add(TrialRecord(organization_id=org.id, tier=tier, started_at=started))
    db.commit()


def _trial_records(db: Session, org: Organization, tier: str | None = None) -> list[TrialRecord]:
    stmt = select(TrialRecord).where(TrialRecord.organization_id == org.id)
    if tier:
        stmt = stmt.where(TrialRecord.tier == tier)
    return list(db.execute(stmt).scalars())


def _utc(value: datetime) -> datetime:
    """sqlite round-trips datetimes naive — normalize for comparison."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def test_signup_org_starts_free_phase(db_session: Session):
    org = _org(db_session)
    assert lifecycle.derive_phase(db_session, org, datetime.now(UTC)) == WorkspacePhase.FREE


def test_first_upgrade_starts_168h_trial(db_session: Session):
    org = _org(db_session)
    now = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
    lifecycle.apply_tier_selection(db_session, org, 'starter', now)
    db_session.refresh(org)

    assert org.subscription_tier == 'starter'
    assert _utc(org.trial_started_at) == now
    assert _utc(org.trial_ends_at) == now + timedelta(hours=168)
    assert lifecycle.derive_phase(db_session, org, now + timedelta(hours=1)) == WorkspacePhase.TRIAL
    records = _trial_records(db_session, org, 'starter')
    assert len(records) == 1


def test_no_invoice_during_trial(db_session: Session):
    org = _org(db_session)
    now = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
    lifecycle.apply_tier_selection(db_session, org, 'starter', now)
    assert list_invoices(db_session, org) == []


def test_retrial_same_tier_silently_blocked(db_session: Session):
    org = _org(db_session)
    now = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
    lifecycle.apply_tier_selection(db_session, org, 'starter', now)
    db_session.refresh(org)

    # Trial runs its course; org falls to limbo.
    trial_end = now + timedelta(hours=168)
    later = trial_end + timedelta(days=2)
    lifecycle.refresh_workspace_state(db_session, org, later)
    assert lifecycle.derive_phase(db_session, org, later) == WorkspacePhase.LIMBO

    # Same tier re-selection must NOT open a second trial.
    lifecycle.apply_tier_selection(db_session, org, 'starter', later)
    db_session.refresh(org)
    assert org.trial_started_at is None
    assert org.trial_ends_at is None
    assert len(_trial_records(db_session, org, 'starter')) == 1
    assert lifecycle.derive_phase(db_session, org, later) == WorkspacePhase.LIMBO


def test_second_tier_gets_own_trial(db_session: Session):
    org = _org(db_session)
    now = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
    lifecycle.apply_tier_selection(db_session, org, 'starter', now)
    db_session.refresh(org)

    # Mid-trial switch to a never-trialed tier starts a fresh 168h trial.
    mid = now + timedelta(hours=24)
    lifecycle.apply_tier_selection(db_session, org, 'scale', mid)
    db_session.refresh(org)

    assert org.subscription_tier == 'scale'
    assert _utc(org.trial_started_at) == mid
    assert _utc(org.trial_ends_at) == mid + timedelta(hours=168)
    assert len(_trial_records(db_session, org, 'scale')) == 1
    assert lifecycle.derive_phase(db_session, org, mid + timedelta(hours=1)) == WorkspacePhase.TRIAL


def test_midtrial_switch_ends_previous_trial(db_session: Session):
    org = _org(db_session)
    now = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
    lifecycle.apply_tier_selection(db_session, org, 'starter', now)
    mid = now + timedelta(hours=24)
    lifecycle.apply_tier_selection(db_session, org, 'scale', mid)

    starter_record = _trial_records(db_session, org, 'starter')[0]
    assert _utc(starter_record.ended_at) == mid
    scale_record = _trial_records(db_session, org, 'scale')[0]
    assert scale_record.ended_at is None


def test_limbo_after_trial_end(db_session: Session):
    org = _org(db_session)
    now = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'starter', now)
    trial_end = now + timedelta(hours=168)
    later = trial_end + timedelta(days=1)

    phase = lifecycle.refresh_workspace_state(db_session, org, later)
    assert phase == WorkspacePhase.LIMBO

    next_start = lifecycle.next_billing_period_start(db_session, org)
    assert next_start == date(2026, 9, 1)
    banner = lifecycle.banner_for(WorkspacePhase.LIMBO, period_start=next_start)
    assert 'Your trial has ended. Your first invoice is due on' in banner['banner_message']
    assert '2026-09-01' in banner['banner_message']


def test_limbo_next_period_start_monthly(db_session: Session):
    org = _org(db_session)
    trial_end = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'starter', trial_end - timedelta(hours=168))
    org.trial_ends_at = trial_end
    db_session.commit()

    assert lifecycle.next_billing_period_start(db_session, org) == date(2026, 9, 1)


def test_limbo_next_period_start_quarterly(db_session: Session):
    org = _org(db_session)
    trial_end = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'scale', trial_end - timedelta(hours=168))
    org.trial_ends_at = trial_end
    db_session.commit()

    assert lifecycle.next_billing_period_start(db_session, org) == date(2026, 10, 1)


def test_refresh_issues_first_invoice_at_boundary(db_session: Session):
    org = _org(db_session)
    trial_end = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'starter', trial_end - timedelta(hours=168))
    org.trial_ends_at = trial_end
    db_session.commit()

    now = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    phase = lifecycle.refresh_workspace_state(db_session, org, now)
    assert phase == WorkspacePhase.GRACE

    invoices = list_invoices(db_session, org)
    assert len(invoices) == 1
    invoice = invoices[0]
    assert invoice.billing_period_start == date(2026, 8, 1)
    assert invoice.billing_period_end == date(2026, 8, 31)
    assert invoice.due_date == date(2026, 8, 1)
    assert invoice.grace_days == 3
    assert invoice.grace_ends_at == date(2026, 8, 4)
    assert invoice.balance_remaining_etb == invoice.total_etb

    warnings = db_session.execute(
        select(Notification).where(
            Notification.organization_id == org.id,
            Notification.kind == 'invoice_warning',
        )
    ).scalars().all()
    assert len(warnings) == 1
    assert _utc(warnings[0].expires_at) == now + timedelta(days=3)


def test_grace_then_hard_lock(db_session: Session):
    org = _org(db_session)
    trial_end = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'starter', trial_end - timedelta(hours=168))
    org.trial_ends_at = trial_end
    db_session.commit()

    grace_now = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    assert lifecycle.refresh_workspace_state(db_session, org, grace_now) == WorkspacePhase.GRACE

    locked_now = datetime(2026, 8, 5, 0, 0, tzinfo=UTC)
    assert lifecycle.refresh_workspace_state(db_session, org, locked_now) == WorkspacePhase.HARD_LOCKED
    banner = lifecycle.banner_for(WorkspacePhase.HARD_LOCKED)
    assert banner['banner_message'] is None


def test_upgrade_during_grace_does_not_reset_grace(db_session: Session):
    org = _org(db_session)
    trial_end = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'starter', trial_end - timedelta(hours=168))
    org.trial_ends_at = trial_end
    db_session.commit()

    grace_now = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    assert lifecycle.refresh_workspace_state(db_session, org, grace_now) == WorkspacePhase.GRACE

    result = lifecycle.apply_tier_selection(db_session, org, 'scale', grace_now)
    assert result.billing_phase == WorkspacePhase.GRACE
    assert len(_trial_records(db_session, org, 'scale')) == 0
    # Grace window untouched by the tier switch (NB-06.4).
    invoice = db_session.execute(
        select(SubscriptionInvoice).where(SubscriptionInvoice.organization_id == org.id)
    ).scalars().one()
    assert invoice.grace_ends_at == date(2026, 8, 4)


def test_tier_switch_from_hard_lock_no_trial(db_session: Session):
    org = _org(db_session)
    trial_end = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)
    _start_trial(db_session, org, 'starter', trial_end - timedelta(hours=168))
    org.trial_ends_at = trial_end
    db_session.commit()

    locked_now = datetime(2026, 8, 5, 0, 0, tzinfo=UTC)
    assert lifecycle.refresh_workspace_state(db_session, org, locked_now) == WorkspacePhase.HARD_LOCKED

    result = lifecycle.apply_tier_selection(db_session, org, 'enterprise', locked_now)
    assert result.billing_phase == WorkspacePhase.HARD_LOCKED
    assert len(_trial_records(db_session, org, 'enterprise')) == 0
    invoice = db_session.execute(
        select(SubscriptionInvoice).where(SubscriptionInvoice.organization_id == org.id)
    ).scalars().one()
    assert invoice.grace_ends_at == date(2026, 8, 4)
