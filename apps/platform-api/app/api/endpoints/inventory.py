from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.db.session import get_db
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.inventory import InventoryOverviewRow, InventoryRead, InventoryUpsert

router = APIRouter()


@router.get('', response_model=list[InventoryRead])
def list_inventory(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    rows = db.execute(select(Inventory)).scalars().all()
    return rows


@router.put('', response_model=InventoryRead)
def upsert_inventory(
    payload: InventoryUpsert,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    warehouse = db.execute(select(Warehouse).where(Warehouse.code == payload.warehouse_code)).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail='Warehouse code not found')

    item = db.execute(select(Item).where(Item.sku == payload.sku)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    inv = db.execute(
        select(Inventory).where(Inventory.warehouse_id == warehouse.id, Inventory.item_id == item.id)
    ).scalar_one_or_none()

    if inv:
        inv.quantity_on_hand = payload.quantity_on_hand
        inv.safety_stock = payload.safety_stock
    else:
        inv = Inventory(
            warehouse_id=warehouse.id,
            item_id=item.id,
            quantity_on_hand=payload.quantity_on_hand,
            safety_stock=payload.safety_stock,
        )

    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get('/overview', response_model=list[InventoryOverviewRow])
def inventory_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    stmt = (
        select(
            Warehouse.code.label('warehouse_code'),
            Warehouse.name.label('warehouse_name'),
            func.coalesce(func.sum(Inventory.quantity_on_hand), 0).label('total_quantity_on_hand'),
            func.coalesce(func.sum(Inventory.safety_stock), 0).label('total_safety_stock'),
            func.max(Warehouse.capacity_units).label('capacity_units'),
        )
        .join(Inventory, Inventory.warehouse_id == Warehouse.id, isouter=True)
        .group_by(Warehouse.code, Warehouse.name)
        .order_by(Warehouse.code)
    )
    rows = db.execute(stmt).all()

    result = []
    for row in rows:
        utilization = (row.total_quantity_on_hand / row.capacity_units * 100.0) if row.capacity_units else 0.0
        result.append(
            InventoryOverviewRow(
                warehouse_code=row.warehouse_code,
                warehouse_name=row.warehouse_name,
                total_quantity_on_hand=int(row.total_quantity_on_hand),
                total_safety_stock=int(row.total_safety_stock),
                utilization_percent=round(utilization, 2),
            )
        )
    return result
