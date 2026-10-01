"""Cash-on-delivery ledger endpoints (NB-86).

The operator question this answers, at the end of every working day: *how much
cash is still out with drivers, and how much never came back?*
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.cash_collection import CashCollection
from app.models.membership import OrganizationMembership
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.shipment import (
    CashCollectionDeclare,
    CashCollectionRead,
    CashCollectionSettle,
    CashCollectionStatus,
    CashLedgerSummary,
)
from app.services import cash_ledger
from app.services.audit import record_audit_event, resolve_actor_organization_id

router = APIRouter()

ZERO = Decimal('0.00')


def _scoped_record(db: Session, record_id: str, organization_id) -> CashCollection:
    return organization_scoped_get(
        db,
        CashCollection,
        record_id,
        organization_id,
        not_found_detail='Cash collection not found',
    )


# NOTE: the static '/ledger' route is declared before '/{record_id}' so the
# suffix is never shadowed by the id pattern (same constraint documented for
# /receipts/audit in app/api/router.py).
@router.get('/ledger', response_model=CashLedgerSummary)
def cash_ledger_summary(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN, UserRole.VIEWER)),
):
    """End-of-day position: outstanding, collected-but-not-banked, shortfall."""
    organization_id = actor_organization_id(actor, db)

    base = scoped_to_organization(
        select(CashCollection).where(CashCollection.status != 'voided'),
        CashCollection,
        organization_id,
    )
    rows = db.execute(base).scalars().all()

    outstanding = [r for r in rows if r.status == 'outstanding']
    collected = [r for r in rows if r.status == 'collected']
    settled = [r for r in rows if r.status == 'settled']

    def total(items: list[CashCollection], attr: str) -> Decimal:
        return sum((getattr(i, attr) or ZERO for i in items), ZERO)

    return CashLedgerSummary(
        outstanding_count=len(outstanding),
        outstanding_expected_etb=total(outstanding, 'expected_etb'),
        collected_count=len(collected),
        collected_etb=total(collected, 'collected_etb'),
        settled_count=len(settled),
        settled_etb=total(settled, 'collected_etb'),
        # Shortfall across everything not yet voided: money the operator is
        # looking for, regardless of whether the record is still open.
        shortfall_etb=total(rows, 'shortfall_etb'),
    )


@router.get('', response_model=list[CashCollectionRead])
def list_cash_collections(
    status: CashCollectionStatus | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN, UserRole.VIEWER)),
):
    stmt = scoped_to_organization(
        select(CashCollection), CashCollection, actor_organization_id(actor, db)
    )
    if status is not None:
        stmt = stmt.where(CashCollection.status == status)
    if driver_id is not None:
        stmt = stmt.where(CashCollection.driver_id == driver_id)
    stmt = stmt.order_by(CashCollection.created_at.desc()).limit(limit)
    return [cash_ledger.serialize(db, r) for r in db.execute(stmt).scalars().all()]


@router.get('/{record_id}', response_model=CashCollectionRead)
def get_cash_collection(
    record_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN, UserRole.VIEWER)),
):
    record = _scoped_record(db, record_id, actor_organization_id(actor, db))
    return cash_ledger.serialize(db, record)


@router.post('/{record_id}/declare', response_model=CashCollectionRead)
def declare_cash(
    record_id: str,
    payload: CashCollectionDeclare,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    """Record what the driver is holding, and surface any shortfall immediately.

    Idempotent: declaring twice with the same figure leaves the same row in the
    same state, so a retry after a dropped connection is safe.
    """
    organization_id = resolve_scoped_organization(actor, writable)
    record = _scoped_record(db, record_id, organization_id)

    if record.status == 'voided':
        raise HTTPException(status_code=409, detail='This cash record was voided')
    if record.status == 'settled':
        raise HTTPException(status_code=409, detail='This cash record is already settled')

    previous_collected = record.collected_etb
    cash_ledger.declare(db, record, collected=payload.collected_etb, note=payload.note)

    record_audit_event(
        db,
        event_type='cash_collection.declared',
        entity_type='cash_collection',
        entity_id=record.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Declared {payload.collected_etb} ETB against shipment cash',
        payload={
            'expected_etb': str(record.expected_etb),
            'previous_collected_etb': str(previous_collected or ZERO),
            'collected_etb': str(record.collected_etb),
            'shortfall_etb': str(record.shortfall_etb),
        },
    )
    db.commit()
    db.refresh(record)
    return cash_ledger.serialize(db, record)


@router.post('/{record_id}/settle', response_model=CashCollectionRead)
def settle_cash(
    record_id: str,
    payload: CashCollectionSettle,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    """Office-side close: the cash is in hand.

    Restricted to admin, matching the receipt-reversal contract: accepting a
    shortfall writes off money, so it is not an operator-level action.
    """
    organization_id = resolve_scoped_organization(actor, writable)
    record = _scoped_record(db, record_id, organization_id)

    if record.status == 'voided':
        raise HTTPException(status_code=409, detail='This cash record was voided')

    already_settled = record.status == 'settled'
    cash_ledger.settle(
        db, record, settled_by=actor.id, note=payload.note
    )

    record_audit_event(
        db,
        event_type='cash_collection.settled',
        entity_type='cash_collection',
        entity_id=record.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=(
            f'Settled cash for shipment (shortfall {record.shortfall_etb} ETB)'
        ),
        payload={
            'expected_etb': str(record.expected_etb),
            'collected_etb': str(record.collected_etb),
            'shortfall_etb': str(record.shortfall_etb),
            'repeat': already_settled,
        },
    )
    db.commit()
    db.refresh(record)
    return cash_ledger.serialize(db, record)
