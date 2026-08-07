from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.security import require_roles, require_writable_workspace
from app.db.session import get_db
from app.models.user import User
from app.models.membership import OrganizationMembership
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services.audit import resolve_actor_organization_id

router = APIRouter()


@router.get('', response_model=list[WarehouseRead])
def list_warehouses(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    organization_id = resolve_actor_organization_id(db, actor)
    query = select(Warehouse)
    if organization_id is not None:
        query = query.where(
            or_(
                Warehouse.organization_id == organization_id,
                Warehouse.organization_id.is_(None),
            )
        )
    rows = db.execute(query.offset(skip).limit(limit)).scalars().all()
    return rows


@router.post('', response_model=WarehouseRead, status_code=201)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    exists_query = select(Warehouse).where(Warehouse.code == payload.code)
    if writable is not None:
        # Equality-only: mirrors the NULL-distinct uq_warehouses_org_code
        # semantics — a legacy null-org row with the same code must NOT
        # false-409 a first org create (TECH-58).
        exists_query = exists_query.where(Warehouse.organization_id == writable.organization_id)
    exists = db.execute(exists_query).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail='Warehouse code already exists')

    warehouse = Warehouse(
        **payload.model_dump(),
        organization_id=writable.organization_id if writable else None,
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get('/{warehouse_id}', response_model=WarehouseRead)
def get_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    row = db.get(Warehouse, warehouse_id)
    organization_id = resolve_actor_organization_id(db, actor)
    if not row or (
        organization_id is not None
        and row.organization_id is not None
        and row.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail='Warehouse not found')
    return row


@router.patch('/{warehouse_id}', response_model=WarehouseRead)
def update_warehouse(
    warehouse_id: str,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    row = db.get(Warehouse, warehouse_id)
    organization_id = resolve_actor_organization_id(db, actor)
    if not row or (
        organization_id is not None
        and row.organization_id is not None
        and row.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail='Warehouse not found')

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
