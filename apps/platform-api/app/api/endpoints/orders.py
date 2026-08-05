from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, require_roles, require_writable_workspace
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.order import HistoricalOrder
from app.models.user import User
from app.repositories import ItemRepository, OrderRepository, WarehouseRepository
from app.schemas.auth import UserRole
from app.schemas.order import HistoricalOrderCreate, HistoricalOrderRead

router = APIRouter()


@router.get('', response_model=list[HistoricalOrderRead])
def list_orders(
    skip: int = 0,
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    repo = OrderRepository(db)
    return repo.list_by_org(membership.organization_id, skip=skip, limit=limit)


@router.post('', response_model=HistoricalOrderRead, status_code=201)
def create_order(
    payload: HistoricalOrderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    membership: OrganizationMembership = Depends(get_current_membership),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    warehouse_repo = WarehouseRepository(db)
    item_repo = ItemRepository(db)
    order_repo = OrderRepository(db)

    warehouse = warehouse_repo.get_by_code(payload.warehouse_code, membership.organization_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail='Warehouse code not found')

    item = item_repo.get_by_sku(payload.sku, membership.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    order = HistoricalOrder(
        order_date=payload.order_date,
        warehouse_id=warehouse.id,
        item_id=item.id,
        organization_id=membership.organization_id,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        customer_region=payload.customer_region,
        weather_avg_temp_c=payload.weather_avg_temp_c,
        weather_precip_mm=payload.weather_precip_mm,
        weather_disruption_index=payload.weather_disruption_index,
    )
    order_repo.add(order)
    order_repo.commit()
    order_repo.refresh(order)
    return order
