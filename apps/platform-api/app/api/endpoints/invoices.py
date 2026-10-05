import io
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    order_by_organization_first,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.order import HistoricalOrder
from app.models.freight_invoice import FreightInvoice
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.invoice import FreightInvoiceRead

router = APIRouter()

@router.get('', response_model=list[FreightInvoiceRead])
def get_invoices(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64 gap: this read carried no tenant scope at all, so every organisation
    # could read every other organisation's freight invoices. Verified against
    # production on 2026-10-05 — a freshly created workspace that had never
    # uploaded anything returned two invoices belonging to a different tenant,
    # while `/notifications` correctly returned none for the same caller.
    #
    # `include_legacy_null=False` is a deliberate departure from the TECH-58
    # default. That default predates multi-tenancy: it exists so a *single-tenant*
    # deployment keeps seeing rows written before org scoping existed. In a
    # genuinely multi-tenant database it does the opposite of its intent — the two
    # unattributed freight invoices created on 2026-09-16 were visible to every
    # tenant that signed up afterwards, which is the leak itself. A financial
    # reconciliation row with no owner belongs to nobody, so it is shown to
    # nobody. Revert this one keyword to restore the old behaviour for reads.
    rows = db.execute(
        scoped_to_organization(
            select(FreightInvoice),
            FreightInvoice,
            actor_organization_id(actor, db),
            include_legacy_null=False,
        )
    ).scalars().all()
    return rows

@router.post('/upload', response_model=list[FreightInvoiceRead])
def upload_invoices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV files are accepted')
    content = file.file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid CSV: {exc}') from exc
    
    required = {'order_id', 'carrier_id', 'actual_rate'}
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')

    organization_id = resolve_scoped_organization(actor, writable)

    results = []
    for _, row in df.iterrows():
        order_id = str(row['order_id'])
        carrier_id = str(row['carrier_id'])
        actual_rate = float(row['actual_rate'])

        # Two leaks closed here. The order lookup had no tenant scope, so an
        # operator could raise an invoice against another organisation's order
        # and read its quantity/unit price back through the computed quoted rate;
        # and the invoice itself was written with organization_id unset, which is
        # what left every historical row unattributed and readable by everyone.
        # `include_legacy_null=False` on a write path so an org-scoped actor can
        # never reconcile against an unattributed row.
        order_stmt = select(HistoricalOrder).where(HistoricalOrder.id == order_id)
        order = db.execute(
            order_by_organization_first(
                scoped_to_organization(
                    order_stmt, HistoricalOrder, organization_id, include_legacy_null=False
                ),
                HistoricalOrder,
            )
        ).scalars().first()
        if not order:
            continue
            
        quoted_rate = order.quantity * order.unit_price
        variance = actual_rate - quoted_rate
        status = 'mismatch_flagged' if variance != 0 else 'matched'
        
        invoice = FreightInvoice(
            organization_id=organization_id,
            order_id=order_id,
            carrier_id=carrier_id,
            quoted_rate=quoted_rate,
            actual_rate=actual_rate,
            variance=variance,
            status=status
        )
        db.add(invoice)
        results.append(invoice)
        
    db.commit()
    for inv in results:
        db.refresh(inv)
        
    return results
