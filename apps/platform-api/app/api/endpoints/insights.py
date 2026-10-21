from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, require_roles
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.decision import (
    CashRiskRow,
    DecisionBrief,
    ExceptionTriageRow,
)
from app.services.decision_intelligence import (
    build_decision_brief,
    cash_risk,
    exception_triage,
)

router = APIRouter()

_READ_ROLES = (UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)


@router.get('/decision-brief', response_model=DecisionBrief)
def get_decision_brief(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(*_READ_ROLES)),
):
    """Return the deterministic, record-grounded daily operating brief.

    The response is assembled from tenant-scoped rows. It is advisory only and
    intentionally has no endpoint that performs the recommended actions.
    """
    return build_decision_brief(db, membership.organization_id)


@router.get('/cash-risk', response_model=list[CashRiskRow])
def get_cash_risk(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(*_READ_ROLES)),
):
    return cash_risk(db, membership.organization_id)


@router.get('/exception-triage', response_model=list[ExceptionTriageRow])
def get_exception_triage(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(*_READ_ROLES)),
):
    return exception_triage(db, membership.organization_id)
