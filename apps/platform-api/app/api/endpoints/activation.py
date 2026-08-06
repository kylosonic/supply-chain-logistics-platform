"""Activation endpoints (blueprint §2.5).

ALL THREE are write-guard EXEMPT by design (receipts precedent): reads
must work while locked, reset must work from a locked workspace, and
pitch-dismiss is a read-adjacent UX action — the free-cap lock can never
dead-end the upgrade path (NB-31.4).

``GET /activation`` commits after composing the read: pitch crossings are
writes-on-read (fire-once semantics need a durable mark — the same lazy
issuance precedent as ``lifecycle.try_issue_invoice``; idempotent via the
UNIQUE constraint).

``POST /activation/reset`` performs NO server-side token invalidation
(stateless JWTs, no blacklist — consistent with the existing auth
design); the console performs the logout + re-login flow client-side
(decision #10).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, require_org_roles
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.activation import (
    ActivationStateRead,
    PitchDismissRequest,
    ResetWorkspaceRequest,
    ResetWorkspaceResult,
)
from app.schemas.auth import OrganizationRole
from app.services.activation import freecap
from app.services.activation import reset as reset_service
from app.services.activation.state import activation_state_read

router = APIRouter()


def _get_org(db: Session, membership: OrganizationMembership) -> Organization:
    org = db.get(Organization, membership.organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail='Organization not found')
    return org


@router.get('', response_model=ActivationStateRead)
def get_activation_state(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    org = _get_org(db, membership)
    state = activation_state_read(db, org, datetime.now(UTC))
    # Pitch crossings are durable writes on this read (see module docstring).
    db.commit()
    return state


@router.post('/reset', response_model=ResetWorkspaceResult)
def reset_workspace_endpoint(
    payload: ResetWorkspaceRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
):
    org = _get_org(db, membership)
    admin_user = db.get(User, membership.user_id)
    try:
        result = reset_service.reset_workspace(
            db, org, admin_user, payload.workspace_name, datetime.now(UTC)
        )
    except reset_service.ResetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    db.commit()
    return ResetWorkspaceResult(**result)


@router.post('/pitch-dismiss')
def dismiss_pitch_endpoint(
    payload: PitchDismissRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.OPERATOR)
    ),
):
    org = _get_org(db, membership)
    dismissed = freecap.dismiss_pitch(db, org, payload.level, datetime.now(UTC))
    db.commit()
    if not dismissed:
        raise HTTPException(status_code=404, detail='No pitch crossing for the current period')
    return {'dismissed': True}
