from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import get_current_membership
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.schemas.billing import SubscriptionInvoiceRead, WorkspaceStateRead
from app.services.billing import invoices as invoices_service
from app.services.billing import lifecycle

router = APIRouter()


@router.get('/invoices', response_model=list[SubscriptionInvoiceRead])
def list_subscription_invoices(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    lifecycle.refresh_workspace_state(db, organization, datetime.now(UTC))
    return invoices_service.list_invoices(db, organization)


@router.get('/invoices/{invoice_number}', response_model=SubscriptionInvoiceRead)
def get_subscription_invoice(
    invoice_number: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    lifecycle.refresh_workspace_state(db, organization, datetime.now(UTC))
    invoice = invoices_service.get_invoice(db, organization, invoice_number)
    if invoice is None:
        raise HTTPException(status_code=404, detail='Invoice not found')
    return invoice


@router.get('/state', response_model=WorkspaceStateRead)
def workspace_state(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    return lifecycle.workspace_state_read(db, organization, datetime.now(UTC))
