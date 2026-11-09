"""Workspace lifecycle state engine (TECH-03, TECH-04, TECH-06).

``billing_phase`` is the authoritative workspace state
(free | trial | limbo | active | grace | hard_locked); legacy
``subscription_status`` is derived for backward compatibility
(blueprint decision #2).

Chain: lifecycle -> invoices -> pricing. HTTP stays out of the state engine.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord
from app.schemas.billing import WorkspacePhase, WorkspaceStateRead
from app.schemas.subscription import SubscriptionRead
from app.services.audit import record_audit_event
from app.services.billing import invoices as invoices_service
from app.services.billing import pricing

LIMBO_BANNER = (
    'Your trial has ended. Your first invoice is due on {period_start} — '
    'once paid, your workspace resumes.'
)
GRACE_BANNER = 'Grace period: {days} days remaining'

WRITE_DISABLED_PHASES = frozenset({WorkspacePhase.LIMBO, WorkspacePhase.GRACE, WorkspacePhase.HARD_LOCKED})

_STATUS_BY_PHASE = {
    WorkspacePhase.FREE: 'active',
    WorkspacePhase.TRIAL: 'trialing',
    WorkspacePhase.LIMBO: 'trialing',
    WorkspacePhase.ACTIVE: 'active',
    WorkspacePhase.GRACE: 'past_due',
    WorkspacePhase.HARD_LOCKED: 'past_due',
}


def _derived_status(phase: WorkspacePhase) -> str:
    return _STATUS_BY_PHASE[phase]


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize naive datetimes (sqlite round-trips) to UTC-aware."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def next_billing_period_start(db: Session, org: Organization) -> date | None:
    """First day of the next billing period after the last trial's end.

    Anchor = last ``TrialRecord.ended_at`` (or started_at + 168h when the
    trial ran its course naturally); Starter -> next month 1st,
    Scale/Enterprise -> next quarter 1st (blueprint decision #4).
    """
    trial = db.execute(
        select(TrialRecord)
        .where(TrialRecord.organization_id == org.id)
        .order_by(TrialRecord.started_at.desc())
    ).scalars().first()
    if trial is None:
        return None
    cycle = pricing.billing_cycle_for(trial.tier)
    if not cycle:
        return None
    ended = _as_utc(trial.ended_at)
    started = _as_utc(trial.started_at)
    anchor = ended or (started + timedelta(hours=pricing.TRIAL_DURATION_HOURS) if started else None)
    if anchor is None:
        return None
    return pricing.next_period_start_after(anchor.date(), cycle)


def derive_phase(db: Session, org: Organization, now: datetime) -> WorkspacePhase:
    """Pure derivation of the authoritative phase — no side effects."""
    has_trial_record = (
        db.execute(
            select(TrialRecord.id).where(TrialRecord.organization_id == org.id).limit(1)
        ).first()
        is not None
    )
    last_invoice = invoices_service.latest_invoice(db, org)

    if last_invoice is None and org.subscription_tier == 'free':
        return WorkspacePhase.FREE
    if last_invoice is None and not has_trial_record and org.trial_started_at is None:
        return WorkspacePhase.FREE

    trial_ends = _as_utc(org.trial_ends_at)
    if trial_ends is None:
        trial_started = _as_utc(org.trial_started_at)
        if trial_started is not None:
            trial_ends = trial_started + timedelta(hours=pricing.TRIAL_DURATION_HOURS)
    if trial_ends is not None and now < trial_ends:
        return WorkspacePhase.TRIAL

    if last_invoice is None:
        return WorkspacePhase.LIMBO

    if last_invoice.balance_remaining_etb > 0:
        if now.date() < last_invoice.grace_ends_at:
            return WorkspacePhase.GRACE
        return WorkspacePhase.HARD_LOCKED
    return WorkspacePhase.ACTIVE


def refresh_workspace_state(db: Session, org: Organization, now: datetime) -> WorkspacePhase:
    """Lazy issuance + derive + persist. Called by every guard evaluation
    and billing-state read."""
    invoices_service.try_issue_invoice(db, org, now)
    phase = derive_phase(db, org, now)
    if org.billing_phase != phase.value:
        org.billing_phase = phase.value
        org.subscription_status = _derived_status(phase)
        db.add(org)
        db.commit()
    return phase


def start_trial(db: Session, org: Organization, tier: str, now: datetime) -> TrialRecord | None:
    """Start a 168h trial for ``tier`` unless that tier was already trialed.

    Returns None (silently blocked, NB-03.5) when a TrialRecord exists for
    the same (organization, tier).
    """
    existing = db.execute(
        select(TrialRecord).where(
            TrialRecord.organization_id == org.id,
            TrialRecord.tier == tier,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return None
    start, _end = pricing.trial_period(now)
    record = TrialRecord(organization_id=org.id, tier=tier, started_at=start)
    db.add(record)
    org.trial_started_at = start
    org.trial_ends_at = start + timedelta(hours=pricing.TRIAL_DURATION_HOURS)
    db.add(org)
    return record


def end_current_trial(db: Session, org: Organization, now: datetime) -> None:
    """Close the open TrialRecord(s); the org no longer has an active trial."""
    open_trials = db.execute(
        select(TrialRecord).where(
            TrialRecord.organization_id == org.id,
            TrialRecord.ended_at.is_(None),
        ).order_by(TrialRecord.started_at.desc())
    ).scalars().all()
    for trial in open_trials:
        trial.ended_at = now
        db.add(trial)
    org.trial_ends_at = now
    db.add(org)


def apply_tier_selection(db: Session, org: Organization, tier: str, now: datetime) -> SubscriptionRead:
    """Select-tier entry point (blueprint decision #3).

    - Trials start only from phase ``free`` and are per-tier, once per tier.
    - Mid-trial switch: current trial closed; new tier never trialed ->
      fresh 168h trial; already trialed -> no trial (limbo).
    - From limbo/grace/hard_locked: tier switches never start trials and
      never reset grace/lock (NB-06.4).
    """
    from_tier = org.subscription_tier
    refresh_workspace_state(db, org, now)
    phase = derive_phase(db, org, now)

    trial_started = False
    trial_ends_at: datetime | None = None

    if tier != 'free':
        if phase == WorkspacePhase.TRIAL and org.subscription_tier != tier:
            end_current_trial(db, org, now)
            # Trial-eligibility context after closing the current trial:
            # no active trial, no invoice — same as a fresh upgrade.
            phase = WorkspacePhase.FREE

        if phase == WorkspacePhase.FREE:
            started = start_trial(db, org, tier, now)
            if started is not None:
                trial_started = True
                trial_ends_at = started.started_at + timedelta(hours=pricing.TRIAL_DURATION_HOURS)
        if not trial_started:
            # No active trial window: either the tier was already trialed
            # (silently blocked) or we are in limbo/grace/hard_locked.
            org.trial_started_at = None
            org.trial_ends_at = None
    else:
        org.trial_started_at = None
        org.trial_ends_at = None

    org.subscription_tier = tier
    final_phase = derive_phase(db, org, now)
    org.billing_phase = final_phase.value
    org.subscription_status = _derived_status(final_phase)
    org.updated_at = now
    db.add(org)
    db.flush()

    record_audit_event(
        db,
        event_type='subscription.tier_selected',
        entity_type='organization',
        entity_id=org.id,
        organization_id=org.id,
        description=f'Changed subscription tier from {from_tier} to {tier}',
        payload={
            'from_tier': from_tier,
            'to_tier': tier,
            'trial_started': trial_started,
            'trial_ends_at': str(trial_ends_at) if trial_ends_at else None,
            'billing_phase': final_phase.value,
        },
    )
    db.commit()
    db.refresh(org)
    return _subscription_read(db, org)


def banner_for(
    phase: WorkspacePhase,
    *,
    period_start: date | None = None,
    days_remaining: int | None = None,
) -> dict[str, Any]:
    """Single source of banner copy per phase."""
    if phase == WorkspacePhase.LIMBO:
        return {
            'banner_message': LIMBO_BANNER.format(period_start=period_start),
            'due_date': period_start,
            'days_remaining': None,
            'can_write': False,
        }
    if phase == WorkspacePhase.GRACE:
        return {
            'banner_message': GRACE_BANNER.format(days=days_remaining),
            'due_date': None,
            'days_remaining': days_remaining,
            'can_write': False,
        }
    return {
        'banner_message': None,
        'due_date': None,
        'days_remaining': None,
        'can_write': phase not in WRITE_DISABLED_PHASES,
    }


def workspace_state_read(db: Session, org: Organization, now: datetime) -> WorkspaceStateRead:
    """Full workspace state surface for GET /billing/state and the guard."""
    phase = refresh_workspace_state(db, org, now)
    last_invoice = invoices_service.latest_invoice(db, org)
    next_start = next_billing_period_start(db, org)

    due_date: date | None = None
    days_remaining: int | None = None
    if phase == WorkspacePhase.GRACE and last_invoice is not None:
        due_date = last_invoice.due_date
        days_remaining = max(0, (last_invoice.grace_ends_at - now.date()).days)
    elif phase == WorkspacePhase.LIMBO:
        due_date = next_start

    banner = banner_for(phase, period_start=next_start if phase == WorkspacePhase.LIMBO else None, days_remaining=days_remaining)
    return WorkspaceStateRead(
        phase=phase,
        can_write=phase not in WRITE_DISABLED_PHASES,
        billing_visible=last_invoice is not None,
        banner_message=banner['banner_message'],
        due_date=due_date,
        days_remaining=days_remaining,
        trial_ends_at=_as_utc(org.trial_ends_at),
        next_billing_period_start=next_start,
    )


def subscription_read(db: Session, org: Organization) -> SubscriptionRead:
    return _subscription_read(db, org)


def _subscription_read(db: Session, org: Organization) -> SubscriptionRead:
    from app.schemas.auth import SubscriptionStatus, SubscriptionTier

    return SubscriptionRead(
        organization_id=org.id,
        organization_name=org.name,
        tier=SubscriptionTier(org.subscription_tier),
        status=SubscriptionStatus(org.subscription_status),
        preferred_ai_provider=org.preferred_ai_provider,
        preferred_ai_key_id=org.preferred_ai_key_id,
        contact_phone=org.contact_phone,
        updated_at=org.updated_at,
        billing_phase=WorkspacePhase(org.billing_phase) if org.billing_phase else None,
        trial_ends_at=org.trial_ends_at,
        next_billing_period_start=next_billing_period_start(db, org),
    )
