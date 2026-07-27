from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.db.session import get_db
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.order import HistoricalOrderCreate, HistoricalOrderRead

router = APIRouter()


@router.get('', response_model=list[HistoricalOrderRead])
def list_orders(
    skip: int = 0,
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    rows = db.execute(
        select(HistoricalOrder).order_by(desc(HistoricalOrder.order_date)).offset(skip).limit(limit)
    ).scalars().all()
    return rows


@router.post('', response_model=HistoricalOrderRead, status_code=201)
def create_order(
    payload: HistoricalOrderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    warehouse = db.execute(select(Warehouse).where(Warehouse.code == payload.warehouse_code)).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail='Warehouse code not found')

    item = db.execute(select(Item).where(Item.sku == payload.sku)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    order = HistoricalOrder(
        order_date=payload.order_date,
        warehouse_id=warehouse.id,
        item_id=item.id,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        customer_region=payload.customer_region,
        weather_avg_temp_c=payload.weather_avg_temp_c,
        weather_precip_mm=payload.weather_precip_mm,
        weather_disruption_index=payload.weather_disruption_index,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
