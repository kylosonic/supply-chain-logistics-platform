"""Activation state engine (blueprint decisions #1/#4/#7).

Milestones 1-5 are DERIVED from real-row presence per category (indexed
EXISTS queries) — nothing stored, so reset (NB-35) resets them
automatically with zero drift. Only milestone 6 + the toast flag +
seeded_at live in ``organization_activation_state``.

N-of-5 = length of the completed PREFIX [warehouses, items, fleet_assets,
inventory, orders] — the sequential rule (decision #1).

Import map: models (5 data tables + activation state), schemas.activation,
services.audit, services.metering, activation.freecap. Never imports
app.api; never imports billing.locks.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activation_state import OrganizationActivationState
from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.organization import Organization
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.activation import ActivationStateRead, CategoryMilestoneRead
from app.services.activation import freecap
from app.services.audit import record_audit_event

CATEGORIES: tuple[str, ...] = ('warehouses', 'items', 'fleet_assets', 'inventory', 'orders')

CATEGORY_META: dict[str, dict] = {
    'warehouses': {'label': 'Warehouses', 'model': Warehouse},
    'items': {'label': 'Items', 'model': Item},
    'fleet_assets': {'label': 'Fleet Assets', 'model': FleetAsset},
    'inventory': {'label': 'Inventory', 'model': Inventory},
    'orders': {'label': 'Orders', 'model': HistoricalOrder},
}


def _real_rows_exist(db: Session, org_id, category: str) -> bool:
    model = CATEGORY_META[category]['model']
    row = db.execute(
        select(model.id).where(
            model.organization_id == org_id,
            model.data_origin == 'real',
        ).limit(1)
    ).first()
    return row is not None


def _row_counts(db: Session, org_id, category: str, origin: str) -> int:
    model = CATEGORY_META[category]['model']
    return db.execute(
        select(func.count())
        .select_from(model)
        .where(model.organization_id == org_id, model.data_origin == origin)
    ).scalar_one()


def completed_prefix(db: Session, org_id) -> int:
    """Longest prefix of CATEGORIES whose real presence is complete."""
    prefix = 0
    for category in CATEGORIES:
        if _real_rows_exist(db, org_id, category):
            prefix += 1
        else:
            break
    return prefix


def next_step(prefix: int) -> dict | None:
    """First incomplete category; None once all 5 are complete."""
    if prefix >= len(CATEGORIES):
        return None
    category = CATEGORIES[prefix]
    return {'category': category, 'label': CATEGORY_META[category]['label'], 'cta': '/upload'}


def _ensure_state_row(db: Session, org_id) -> OrganizationActivationState:
    state = db.execute(
        select(OrganizationActivationState).where(
            OrganizationActivationState.organization_id == org_id
        )
    ).scalar_one_or_none()
    if state is None:
        state = OrganizationActivationState(organization_id=org_id)
        db.add(state)
        db.flush()
    return state


def record_csv_upload(
    db: Session,
    org_id,
    actor: User | None,
    *,
    category: str,
    counts: dict,
    now: datetime,
) -> None:
    """Audit a real CSV upload (decision #4 gap-fill). NO milestone writes."""
    record_audit_event(
        db,
        event_type='workspace.csv_uploaded',
        entity_type='organization',
        entity_id=org_id,
        actor=actor,
        organization_id=org_id,
        description=f'Uploaded {category} CSV with real data',
        payload={
            'category': category,
            'data_origin': 'real',
            'records_processed': counts.get('records_processed', 0),
            'records_created': counts.get('records_created', 0),
            'records_updated': counts.get('records_updated', 0),
            'errors': counts.get('errors', []),
        },
    )


def record_route_optimization(
    db: Session,
    org_id,
    run_id,
    *,
    data_origin: str,
    now: datetime,
) -> bool:
    """Register milestone 6 on the org's FIRST route optimization run.

    Returns True iff this was the first transition (m6 set + toast flag +
    audit). False when m6 already set — no re-fire (server truth).
    Commit-aware: the caller commits.
    """
    state = _ensure_state_row(db, org_id)
    if state.m6_completed_at is not None:
        return False

    state.m6_completed_at = now
    state.toast_fired_at = now
    db.add(state)

    record_audit_event(
        db,
        event_type='activation.milestone_6_completed',
        entity_type='route_optimization_run',
        entity_id=run_id,
        organization_id=org_id,
        description='First route optimization completed — milestone 6',
        payload={
            'first_route_optimization_run_id': run_id,
            'data_origin': data_origin,
        },
    )
    return True


def _banner_fragment(*, visible: bool, n_of_5: int, pct_complete: int, demo_mode: bool) -> dict:
    cta: str | None = None
    if visible:
        cta = '/routes' if n_of_5 == 5 else '/upload'
    return {
        'visible': visible,
        'n_of_5': n_of_5,
        'pct_complete': pct_complete,
        'cta': cta,
        'demo_mode': demo_mode,
    }


def activation_state_read(db: Session, org: Organization, now: datetime) -> ActivationStateRead:
    """Full activation-state composition (blueprint §2.3).

    Fires pitch crossings via ``freecap.pitch_state`` (write-on-read, lazy
    issuance precedent). The caller commits (endpoint-level).
    """
    state = _ensure_state_row(db, org.id)
    prefix = completed_prefix(db, org.id)
    m6_completed = state.m6_completed_at is not None

    milestones: list[CategoryMilestoneRead] = []
    for index, category in enumerate(CATEGORIES):
        real_rows = _row_counts(db, org.id, category, 'real')
        sample_rows = _row_counts(db, org.id, category, 'sample')
        status = 'real' if real_rows else ('sample' if sample_rows else 'empty')
        milestones.append(
            CategoryMilestoneRead(
                category=category,
                label=CATEGORY_META[category]['label'],
                status=status,
                real_rows=real_rows,
                sample_rows=sample_rows,
                completed=index < prefix,
            )
        )

    pct = min(prefix * 20, 80)
    cap = freecap.free_cap_state(db, org, now)
    return ActivationStateRead(
        organization_id=str(org.id),
        n_of_5=prefix,
        pct_complete=pct,
        milestones=milestones,
        m6_completed=m6_completed,
        m6_completed_at=state.m6_completed_at,
        next_step=next_step(prefix),
        banner=_banner_fragment(
            visible=not m6_completed,
            n_of_5=prefix,
            pct_complete=pct,
            demo_mode=prefix < 5,
        ),
        free_cap={
            'locked': cap.locked,
            'utilization_pct': cap.utilization_pct,
            'message': cap.message,
        },
        pitch=freecap.pitch_state(db, org, now),
        toast_fired=state.toast_fired_at is not None,
    )
