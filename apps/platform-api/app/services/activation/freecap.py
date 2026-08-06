"""Free-tier cap lock and upgrade-pitch ladder (blueprint decisions #5/#6).

Pure lazy derivation, zero cron: the lock derives from the CURRENT month
usage window exactly like Phase 1 phase derivation — month rollover lifts
the lock for free (the window moves, counters read zero for the new
period).

``pitch_state`` performs crossing INSERTs on read (fire-once needs a
durable mark — the same lazy-issuance precedent as
``lifecycle.try_issue_invoice``; the endpoint is write-guard exempt and
idempotent via the UNIQUE constraint).

Import map (LEAF of billing): models.usage_meter, models.organization,
services.metering, services.billing.pricing. Imports nothing from the
rest of activation — pure counter math, acyclic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.threshold_crossing import ThresholdCrossing
from app.models.usage_meter import OrganizationUsageCounter
from app.services.audit import record_audit_event
from app.services.billing import pricing
from app.services.metering import current_usage_window

FREE_CAP_MESSAGE = (
    'Free tier cap reached. Writes resume next month, or upgrade now to continue immediately.'
)

_METRICS = ('delivery_tasks', 'route_optimizations')


@dataclass
class FreeCapState:
    locked: bool
    utilization_pct: int
    message: str | None
    period_start: date


class FreeCapLockedError(Exception):
    """Raised when the Free tier monthly cap is hit (decision #5).

    Mirrors ``billing.locks.WorkspaceLockedError``; ``state`` carries the
    derivation for the 423 detail.
    """

    def __init__(self, state: FreeCapState) -> None:
        self.state = state
        super().__init__(FREE_CAP_MESSAGE)


def _counter_used_units(db: Session, org_id, metric: str, period_start: date) -> int:
    counter = db.execute(
        select(OrganizationUsageCounter).where(
            OrganizationUsageCounter.organization_id == org_id,
            OrganizationUsageCounter.metric == metric,
            OrganizationUsageCounter.period_start == period_start,
        )
    ).scalar_one_or_none()
    return counter.used_units if counter is not None else 0


def _pct(used_units: int, included_units: int | None) -> int | None:
    if included_units is None or included_units <= 0:
        return None
    return int(round(used_units / included_units * 100))


def free_cap_state(db: Session, org: Organization, now: datetime) -> FreeCapState:
    """Pure lazy derivation of the Free-cap lock (decision #5). No writes."""
    period_start, _period_end = current_usage_window(now.date())
    tier = org.subscription_tier

    per_metric: list[tuple[str, int, int | None]] = []
    pcts: list[int] = []
    for metric in _METRICS:
        included = pricing.included_units(tier, metric)
        used = _counter_used_units(db, org.id, metric, period_start)
        per_metric.append((metric, used, included))
        pct = _pct(used, included)
        if pct is not None:
            pcts.append(pct)

    utilization_pct = max(pcts) if pcts else 0
    locked = tier == 'free' and any(
        included is not None and used >= included for _metric, used, included in per_metric
    )
    return FreeCapState(
        locked=locked,
        utilization_pct=utilization_pct,
        message=FREE_CAP_MESSAGE if locked else None,
        period_start=period_start,
    )


def assert_free_cap_writable(db: Session, org: Organization, now: datetime) -> FreeCapState:
    """Raise ``FreeCapLockedError`` when the cap holds; else return state."""
    state = free_cap_state(db, org, now)
    if state.locked:
        raise FreeCapLockedError(state)
    return state


def _crossing(db: Session, org_id, period_start: date, level: str) -> ThresholdCrossing | None:
    return db.execute(
        select(ThresholdCrossing).where(
            ThresholdCrossing.organization_id == org_id,
            ThresholdCrossing.period_start == period_start,
            ThresholdCrossing.threshold_level == level,
        )
    ).scalar_one_or_none()


def pitch_state(db: Session, org: Organization, now: datetime) -> dict:
    """Cross + compose the pitch payload fragment (decision #6).

    Fires (INSERT + audit) any threshold <= current utilization not yet
    crossed this period. Non-free tiers carry no pitch.
    """
    if org.subscription_tier != 'free':
        return {'banner': None, 'dismissible': False, 'fired': []}

    state = free_cap_state(db, org, now)
    period_start = state.period_start
    utilization_pct = state.utilization_pct
    fired: list[str] = []

    for level, threshold in (('p60', 60), ('p80', 80)):
        if utilization_pct >= threshold and _crossing(db, org.id, period_start, level) is None:
            db.add(
                ThresholdCrossing(
                    organization_id=org.id,
                    period_start=period_start,
                    threshold_level=level,
                    fired_at=now,
                )
            )
            record_audit_event(
                db,
                event_type='usage.pitch_fired',
                entity_type='organization',
                entity_id=org.id,
                organization_id=org.id,
                description=f'Fired {level} upgrade pitch at {utilization_pct}% utilization',
                payload={
                    'level': level,
                    'period_start': str(period_start),
                    'utilization_pct': utilization_pct,
                },
            )
            fired.append(level)

    # Flush so the banner reads below see freshly inserted crossings even
    # under autoflush=False sessions (guard/endpoint sessions).
    db.flush()

    p60 = _crossing(db, org.id, period_start, 'p60')
    p80 = _crossing(db, org.id, period_start, 'p80')

    if state.locked:
        banner: str | None = 'p100'
    elif p80 is not None:
        banner = 'p80'
    elif p60 is not None and p60.dismissed_at is None:
        banner = 'p60'
    else:
        banner = None

    return {'banner': banner, 'dismissible': banner == 'p60', 'fired': fired}


def dismiss_pitch(db: Session, org: Organization, level: str, now: datetime) -> bool:
    """Mark the current-period crossing dismissed. False when no row (404)."""
    period_start, _period_end = current_usage_window(now.date())
    row = _crossing(db, org.id, period_start, level)
    if row is None:
        return False
    row.dismissed_at = now
    db.add(row)
    return True
