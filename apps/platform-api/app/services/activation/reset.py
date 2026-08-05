"""Admin-gated workspace reset to sample data (decision #10 / NB-35).

One transaction: wipe ALL org-scoped rows of the 5 categories (reverse
dependency order), re-seed from the shipped CSVs, reset the activation
state, clear pitch crossings, and audit ``workspace.reset_to_sample_data``
with the admin user + timestamp.

No server-side token invalidation exists (stateless JWTs, no blacklist —
consistent with the existing auth design); the console performs the
logout + re-login flow client-side.

Import map: models (5 tables + activation state + crossings),
activation.seeding, activation.state, services.audit. Never app.api.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.organization import Organization
from app.models.threshold_crossing import ThresholdCrossing
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.activation import seeding
from app.services.activation.state import CATEGORIES, _ensure_state_row
from app.services.audit import record_audit_event

_DELETE_ORDER = (HistoricalOrder, Inventory, FleetAsset, Item, Warehouse)


class ResetError(Exception):
    """Carries an HTTP status for the endpoint (422 on name mismatch)."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def reset_workspace(
    db: Session,
    org: Organization,
    admin_user: User,
    workspace_name: str,
    now: datetime,
) -> dict:
    """Reset the org to its seeded sample-data state (decision #10)."""
    if workspace_name.strip() != org.name:
        raise ResetError(422, 'Workspace name does not match')

    # (a) delete ALL org-scoped rows, reverse dependency order.
    for model in _DELETE_ORDER:
        db.execute(delete(model).where(model.organization_id == org.id))

    # (b) re-seed sample rows (force=True — rows already wiped).
    seed_result = seeding.seed_workspace(db, org, admin_user, force=True, now=now)
    rows_reseeded: dict = seed_result['rows_per_category']

    # (c) activation state resets: m6/toast cleared, seeded_at refreshed.
    state = _ensure_state_row(db, org.id)
    state.m6_completed_at = None
    state.toast_fired_at = None
    state.seeded_at = now
    db.add(state)

    # (d) pitch crossings cleared (NB-35).
    db.execute(delete(ThresholdCrossing).where(ThresholdCrossing.organization_id == org.id))

    # (e) audit with admin user + timestamp (NB-35.5).
    record_audit_event(
        db,
        event_type='workspace.reset_to_sample_data',
        entity_type='organization',
        entity_id=org.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Reset workspace {org.name} to sample data',
        payload={
            'workspace_name': org.name,
            'categories': list(CATEGORIES),
            'rows_reseeded': rows_reseeded,
        },
    )
    return {'rows_reseeded': rows_reseeded, 'activation_reset': True}
