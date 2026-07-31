import io
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.db.session import get_db
from app.models.order import HistoricalOrder
from app.models.freight_invoice import FreightInvoice
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.invoice import FreightInvoiceRead

router = APIRouter()

@router.get('', response_model=list[FreightInvoiceRead])
def get_invoices(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    rows = db.execute(select(FreightInvoice)).scalars().all()
    return rows

@router.post('/upload', response_model=list[FreightInvoiceRead])
def upload_invoices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
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

    results = []
    for _, row in df.iterrows():
        order_id = str(row['order_id'])
        carrier_id = str(row['carrier_id'])
        actual_rate = float(row['actual_rate'])
        
        order = db.execute(select(HistoricalOrder).where(HistoricalOrder.id == order_id)).scalar_one_or_none()
        if not order:
            continue
            
        quoted_rate = order.quantity * order.unit_price
        variance = actual_rate - quoted_rate
        status = 'mismatch_flagged' if variance != 0 else 'matched'
        
        invoice = FreightInvoice(
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
