from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import require_roles, require_writable_workspace
from app.db.session import get_db
from app.models.user import User
from app.models.membership import OrganizationMembership
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate

router = APIRouter()


@router.get('', response_model=list[WarehouseRead])
def list_warehouses(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    rows = db.execute(select(Warehouse).offset(skip).limit(limit)).scalars().all()
    return rows


@router.post('', response_model=WarehouseRead, status_code=201)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    exists = db.execute(select(Warehouse).where(Warehouse.code == payload.code)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail='Warehouse code already exists')

    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get('/{warehouse_id}', response_model=WarehouseRead)
def get_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    row = db.get(Warehouse, warehouse_id)
    if not row:
        raise HTTPException(status_code=404, detail='Warehouse not found')
    return row


@router.patch('/{warehouse_id}', response_model=WarehouseRead)
def update_warehouse(
    warehouse_id: str,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    row = db.get(Warehouse, warehouse_id)
    if not row:
        raise HTTPException(status_code=404, detail='Warehouse not found')

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
