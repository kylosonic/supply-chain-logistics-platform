from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, require_roles
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.repositories import InventoryRepository, ItemRepository, WarehouseRepository
from app.schemas.auth import UserRole
from app.schemas.inventory import InventoryOverviewRow, InventoryRead, InventoryUpsert

router = APIRouter()


@router.get('', response_model=list[InventoryRead])
def list_inventory(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    repo = InventoryRepository(db)
    return repo.list_by_org(membership.organization_id)


@router.put('', response_model=InventoryRead)
def upsert_inventory(
    payload: InventoryUpsert,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    warehouse_repo = WarehouseRepository(db)
    item_repo = ItemRepository(db)
    inv_repo = InventoryRepository(db)

    warehouse = warehouse_repo.get_by_code(payload.warehouse_code, membership.organization_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail='Warehouse code not found')

    item = item_repo.get_by_sku(payload.sku, membership.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    inv = inv_repo.upsert(
        warehouse_id=warehouse.id,
        item_id=item.id,
        organization_id=membership.organization_id,
        quantity_on_hand=payload.quantity_on_hand,
        safety_stock=payload.safety_stock,
    )
    return inv


@router.get('/overview', response_model=list[InventoryOverviewRow])
def inventory_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    repo = InventoryRepository(db)
    rows = repo.get_overview_by_org(membership.organization_id)

    result = []
    for row in rows:
        utilization = (row['total_quantity_on_hand'] / row['capacity_units'] * 100.0) if row['capacity_units'] else 0.0
        result.append(
            InventoryOverviewRow(
                warehouse_code=row['warehouse_code'],
                warehouse_name=row['warehouse_name'],
                total_quantity_on_hand=int(row['total_quantity_on_hand']),
                total_safety_stock=int(row['total_safety_stock']),
                utilization_percent=round(utilization, 2),
            )
        )
    return result
