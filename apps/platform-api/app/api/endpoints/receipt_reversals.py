"""Reversal endpoints (TECH-18..21 / NB-18..21) — prefix ``/receipts``.

Registered AFTER ``receipts.router`` in ``api/router.py`` so the static
suffixes ``/audit`` and ``/trusted-payers`` are never swallowed by a
``{receipt_id}`` pattern (the receipts router has no ``GET /{receipt_id}``
route — no conflicts; verified by ``test_route_registration_no_conflicts``).

Server-side window enforcement (decision #7): availability is computed here
against ``receipt.decided_at + 24h`` at every read AND re-checked inside
the services at every write — the UI hiding an Undo button is UX only.

Cross-org admin pattern (decision #10): admin-only endpoints act on the
RECEIPT's organization, never the admin's membership org; the trusted-payer
removal endpoint takes ``organization_id`` as a query param for the same
reason (blueprint risk #7).

WRITE-GUARD EXEMPT (same carve-out as Phase 2): undo/reverse/removal
service locked workspaces — that is the feature's purpose.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import get_current_user, require_org_roles
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.user import User
from app.schemas.auth import OrganizationRole
from app.schemas.receipts import (
    ReceiptAuditEventRead,
    ReversalRead,
    ReverseRequest,
    UndoRequest,
    VerifiedReceiptAuditRead,
)
from app.services.billing.receipts import queue as queue_service
from app.services.billing.reversals import (
    ReversalError,
    reversal_availability,
    reverse_verification,
    undo_verification,
)
from app.services.billing.reversals.reverse import build_reversal_message
from app.services.billing.trusted_payers import remove_trusted_payer

router = APIRouter()


def _as_http(exc: ReversalError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


def _reversal_read(db: Session, receipt: PaymentReceipt) -> ReversalRead:
    """Build the read from the receipt + the reversal audit record (the
    reversal's source of truth for the restored/voided amounts)."""
    event = db.execute(
        select(AuditEvent).where(
            AuditEvent.entity_type == 'payment_receipt',
            AuditEvent.entity_id == str(receipt.id),
            AuditEvent.event_type.in_(['receipts.undo', 'receipts.reversed']),
        ).order_by(AuditEvent.created_at.desc()).limit(1)
    ).scalars().first()
    payload = event.payload if event is not None else {}
    message = None
    if payload.get('decision') == 'reversed':
        message = build_reversal_message(payload, receipt.decided_at, payload.get('note') or '')
    return ReversalRead(
        receipt_id=str(receipt.id),
        invoice_number=receipt.invoice.invoice_number if receipt.invoice else None,
        reference_number=receipt.reference_number,
        amount_etb=receipt.amount_etb,
        reversal_status=receipt.reversal_status,
        reversal_note=receipt.reversal_note,
        reversed_at=receipt.reversed_at,
        restored_balance_etb=(
            Decimal(payload['restored_balance_etb']) if payload.get('restored_balance_etb') else None
        ),
        wallet_voided_etb=(
            Decimal(payload['wallet_voided_etb']) if payload.get('wallet_voided_etb') else None
        ),
        message=message,
    )


@router.get('/audit', response_model=list[VerifiedReceiptAuditRead])
def receipt_audit_list(
    db: Session = Depends(get_db),
    _membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
):
    """All verified receipts, newest decision first, each with server-side
    reversal availability (decision #7). Write-guard EXEMPT."""
    now = datetime.now(UTC)
    rows = []
    for receipt in queue_service.list_verified(db):
        org = db.get(Organization, receipt.organization_id)
        rows.append(
            VerifiedReceiptAuditRead(
                id=receipt.id,
                organization_id=receipt.organization_id,
                organization_name=org.name if org else '',
                invoice_number=receipt.invoice.invoice_number if receipt.invoice else None,
                reference_number=receipt.reference_number,
                amount_etb=receipt.amount_etb,
                sender_name=receipt.sender_name,
                decided_at=receipt.decided_at,
                reversal_status=receipt.reversal_status,
                **reversal_availability(db, receipt, now),
            )
        )
    return rows


@router.get('/{receipt_id}/audit-events', response_model=list[ReceiptAuditEventRead])
def receipt_audit_events(
    receipt_id: str,
    db: Session = Depends(get_db),
    _membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
):
    """The per-receipt audit timeline, newest first (NB-18.1). The Undo/
    Reverse affordance is anchored ON the ``receipts.verified`` event
    (NB-19.1/NB-20.1): ``available_actions`` is computed server-side for
    that event only, while ``reversal_status IS NULL``."""
    receipt = db.get(PaymentReceipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail='Receipt not found')
    events = db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == 'payment_receipt',
            AuditEvent.entity_id == str(receipt.id),
        )
        .order_by(AuditEvent.created_at.desc())
    ).scalars().all()
    availability = reversal_availability(db, receipt, datetime.now(UTC))
    actions: list[str] = []
    if availability['undo_available']:
        actions = ['undo']
    elif availability['reverse_available']:
        actions = ['reverse']
    return [
        ReceiptAuditEventRead(
            id=str(event.id),
            event_type=event.event_type,
            description=event.description,
            created_at=event.created_at,
            payload=event.payload,
            available_actions=actions if event.event_type == 'receipts.verified' else [],
        )
        for event in events
    ]


@router.post('/{receipt_id}/undo', response_model=ReversalRead)
def undo_receipt_endpoint(
    receipt_id: str,
    payload: UndoRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
):
    """Silent Undo (NB-19) — all guards live in ``undo.undo_verification``;
    the server 409s past the 24h window (decision #7). Write-guard EXEMPT."""
    try:
        receipt = undo_verification(db, user, receipt_id, note=payload.note)
    except ReversalError as exc:
        raise _as_http(exc) from None
    db.commit()  # when the refresh did not commit (phase unchanged)
    return _reversal_read(db, receipt)


@router.post('/{receipt_id}/reverse', response_model=ReversalRead)
def reverse_receipt_endpoint(
    receipt_id: str,
    payload: ReverseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
):
    """Explicit Reverse (NB-20) — mandatory reason, exact NB-20.3 customer
    notification, NO refund. Write-guard EXEMPT."""
    try:
        receipt = reverse_verification(db, user, receipt_id, payload.reason)
    except ReversalError as exc:
        raise _as_http(exc) from None
    db.commit()  # when the refresh did not commit (phase unchanged)
    return _reversal_read(db, receipt)


@router.delete('/trusted-payers/{sender_name}')
def remove_trusted_payer_endpoint(
    sender_name: str,
    organization_id: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _membership: OrganizationMembership = Depends(
        require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    ),
):
    """Admin-only trusted-payer removal (NB-21.5). Org context comes from the
    query param — the admin queue is system-wide and the admin's membership
    org must NOT be used (blueprint risk #7). Missing row -> 404. The fraud
    flag is NOT cleared (decision #6). Write-guard EXEMPT."""
    org = db.get(Organization, organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail='Organization not found')
    removed = remove_trusted_payer(db, org, sender_name, user)
    if not removed:
        raise HTTPException(status_code=404, detail='Trusted payer not found')
    db.commit()
    return {'removed': True}
