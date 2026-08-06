"""Write-lock enforcement policy (TECH-06 / NB-06 + Phase 4 decision #5).

Chain: locks -> lifecycle -> invoices -> pricing.

Phase 4 addition: the Free-tier meter gate COMPOSES inside
``assert_workspace_writable`` — one guard chain, zero per-endpoint edits.
``can_write = phase not in WRITE_DISABLED_PHASES AND NOT free_cap_locked``.
Import direction: ``billing.locks -> activation.freecap -> pricing`` has no
back-edge into billing (activation imports pricing reads only, never
locks/lifecycle) — acyclic by construction.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.schemas.billing import WorkspacePhase, WorkspaceStateRead
from app.services.activation import freecap
from app.services.billing import lifecycle

WRITE_DISABLED_PHASES = frozenset({WorkspacePhase.LIMBO, WorkspacePhase.GRACE, WorkspacePhase.HARD_LOCKED})

# ADJUDICATED (blueprint decision #5): NB-06.3 acceptance criteria wins —
# grace is write-disabled. Behavior doc §5.6 wording is superseded.
GRACE_WRITES_ENABLED = False


class WorkspaceLockedError(Exception):
    """Raised when the workspace is in a write-disabled phase."""

    def __init__(self, state: WorkspaceStateRead) -> None:
        self.state = state
        super().__init__(f'Workspace is in phase {state.phase.value}')


def assert_workspace_writable(
    db: Session,
    membership: OrganizationMembership,
    now: datetime | None = None,
) -> OrganizationMembership:
    """Refresh workspace state (incl. lazy invoice issuance) and raise
    ``WorkspaceLockedError`` when the phase is write-disabled, then
    evaluate the Phase 4 Free-tier meter gate (decision #5) — the phase
    lock wins on priority; the free-cap lock re-surfaces when the phase
    resolves."""
    org = db.get(Organization, membership.organization_id)
    if org is None:
        # No workspace row: nothing to lock (fail-open for org-less calls).
        return membership

    reference = now or datetime.now(UTC)
    state = lifecycle.workspace_state_read(db, org, reference)

    disabled = set(WRITE_DISABLED_PHASES)
    if not GRACE_WRITES_ENABLED:
        disabled.add(WorkspacePhase.GRACE)

    if state.phase in disabled:
        raise WorkspaceLockedError(state)

    freecap.assert_free_cap_writable(db, org, reference)
    return membership
