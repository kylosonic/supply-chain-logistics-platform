from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.security import require_roles, require_writable_workspace
from app.db.session import get_db
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate
from app.services.audit import resolve_actor_organization_id

router = APIRouter()


@router.get('', response_model=list[ItemRead])
def list_items(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    organization_id = resolve_actor_organization_id(db, actor)
    query = select(Item)
    if organization_id is not None:
        query = query.where(
            or_(
                Item.organization_id == organization_id,
                Item.organization_id.is_(None),
            )
        )
    rows = db.execute(query.offset(skip).limit(limit)).scalars().all()
    return rows


@router.post('', response_model=ItemRead, status_code=201)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    exists_query = select(Item).where(Item.sku == payload.sku)
    if writable is not None:
        # Equality-only: mirrors the NULL-distinct uq_items_org_sku
        # semantics — a legacy null-org row with the same sku must NOT
        # false-409 a first org create (TECH-58).
        exists_query = exists_query.where(Item.organization_id == writable.organization_id)
    exists = db.execute(exists_query).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail='SKU already exists')

    item = Item(
        **payload.model_dump(),
        organization_id=writable.organization_id if writable else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get('/{item_id}', response_model=ItemRead)
def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    row = db.get(Item, item_id)
    organization_id = resolve_actor_organization_id(db, actor)
    if not row or (
        organization_id is not None
        and row.organization_id is not None
        and row.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail='Item not found')
    return row


@router.patch('/{item_id}', response_model=ItemRead)
def update_item(
    item_id: str,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    row = db.get(Item, item_id)
    organization_id = resolve_actor_organization_id(db, actor)
    if not row or (
        organization_id is not None
        and row.organization_id is not None
        and row.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail='Item not found')

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
