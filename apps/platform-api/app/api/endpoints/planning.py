from __future__ import annotations

from datetime import UTC, datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    get_current_user,
    order_by_organization_first,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.order import HistoricalOrder
from app.models.replenishment import ReplenishmentPlan
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.planning import (
    ReplenishmentApproveRequest,
    ReplenishmentGenerateRequest,
    ReplenishmentPlanRead,
    ReplenishmentPlanStatus,
    ReplenishmentRejectRequest,
)
from app.services.audit import record_audit_event, resolve_actor_organization_id

router = APIRouter()


def _to_read(plan: ReplenishmentPlan, warehouse_code: str, sku: str) -> ReplenishmentPlanRead:
    return ReplenishmentPlanRead(
        id=plan.id,
        created_at=plan.created_at,
        warehouse_code=warehouse_code,
        sku=sku,
        horizon_weeks=plan.horizon_weeks,
        avg_weekly_demand=round(plan.avg_weekly_demand, 2),
        suggested_quantity=plan.suggested_quantity,
        approved_quantity=plan.approved_quantity,
        status=ReplenishmentPlanStatus(plan.status),
        rationale=plan.rationale,
        created_by_user_id=plan.created_by_user_id,
        approved_by_user_id=plan.approved_by_user_id,
        approved_at=plan.approved_at,
        rejection_reason=plan.rejection_reason,
    )


@router.get('/replenishment', response_model=list[ReplenishmentPlanRead])
def list_replenishment_plans(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64 (audit H-1): replenishment plans are tenant data.
    stmt = scoped_to_organization(
        select(ReplenishmentPlan, Warehouse.code, Item.sku)
        .join(Warehouse, Warehouse.id == ReplenishmentPlan.warehouse_id)
        .join(Item, Item.id == ReplenishmentPlan.item_id),
        ReplenishmentPlan,
        actor_organization_id(actor, db),
    )
    rows = db.execute(stmt.order_by(asc(ReplenishmentPlan.created_at))).all()
    return [_to_read(row.ReplenishmentPlan, row.code, row.sku) for row in rows]


@router.post('/replenishment/generate', response_model=list[ReplenishmentPlanRead])
def generate_replenishment_plans(
    payload: ReplenishmentGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    if user.role not in {UserRole.OPERATOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail='Insufficient role')

    # NB-64: generate only from the caller's own inventory and order history,
    # and stamp the plan with the caller's org.
    organization_id = writable.organization_id if writable else None

    inventory_stmt = scoped_to_organization(
        select(Inventory, Warehouse.code, Item.sku, Item.reorder_level).join(Warehouse).join(Item),
        Inventory,
        organization_id,
    )
    inventories = db.execute(inventory_stmt).all()
    order_stmt = scoped_to_organization(select(HistoricalOrder), HistoricalOrder, organization_id)
    orders = db.execute(order_stmt).scalars().all()

    demand_by_pair: dict[tuple[str, str], dict[str, int | datetime.date | None]] = {}
    for order in orders:
        key = (order.warehouse_id, order.item_id)
        entry = demand_by_pair.get(key)
        if not entry:
            demand_by_pair[key] = {'total_qty': order.quantity, 'min_date': order.order_date, 'max_date': order.order_date}
            continue
        entry['total_qty'] = int(entry['total_qty']) + order.quantity
        entry['min_date'] = min(entry['min_date'], order.order_date) if entry['min_date'] else order.order_date
        entry['max_date'] = max(entry['max_date'], order.order_date) if entry['max_date'] else order.order_date

    created: list[tuple[ReplenishmentPlan, str, str]] = []
    for row in inventories:
        key = (row.Inventory.warehouse_id, row.Inventory.item_id)
        agg = demand_by_pair.get(key)
        if agg:
            total_qty = int(agg['total_qty'])
            min_date = agg['min_date']
            max_date = agg['max_date']
            observed_days = ((max_date - min_date).days + 1) if min_date and max_date else 7
            observed_weeks = max(1, ceil(observed_days / 7))
            avg_weekly = total_qty / observed_weeks
        else:
            avg_weekly = float(row.reorder_level) / max(payload.horizon_weeks, 1)

        projected = ceil(avg_weekly * payload.horizon_weeks)
        suggested = max(0, projected + row.Inventory.safety_stock - row.Inventory.quantity_on_hand)
        if suggested <= 0:
            continue

        existing_pending = db.execute(
            order_by_organization_first(
                scoped_to_organization(
                    select(ReplenishmentPlan).where(
                        ReplenishmentPlan.warehouse_id == row.Inventory.warehouse_id,
                        ReplenishmentPlan.item_id == row.Inventory.item_id,
                        ReplenishmentPlan.status == ReplenishmentPlanStatus.PENDING_APPROVAL,
                    ),
                    ReplenishmentPlan,
                    organization_id,
                ),
                ReplenishmentPlan,
            )
        ).scalars().first()
        if existing_pending:
            continue

        plan = ReplenishmentPlan(
            organization_id=organization_id,
            warehouse_id=row.Inventory.warehouse_id,
            item_id=row.Inventory.item_id,
            horizon_weeks=payload.horizon_weeks,
            avg_weekly_demand=avg_weekly,
            suggested_quantity=suggested,
            status=ReplenishmentPlanStatus.PENDING_APPROVAL,
            rationale=f'Projected demand {projected} + safety stock {row.Inventory.safety_stock} - on hand {row.Inventory.quantity_on_hand}',
            created_by_user_id=user.id,
        )
        db.add(plan)
        created.append((plan, row.code, row.sku))

    record_audit_event(
        db,
        event_type='planning.replenishment_generated',
        entity_type='replenishment_plan',
        actor=user,
        organization_id=resolve_actor_organization_id(db, user),
        description=f'Generated {len(created)} replenishment plans',
        payload={'generated_count': len(created), 'horizon_weeks': payload.horizon_weeks},
    )

    db.commit()
    result: list[ReplenishmentPlanRead] = []
    for plan, warehouse_code, sku in created:
        db.refresh(plan)
        result.append(_to_read(plan, warehouse_code, sku))
    return result


@router.post('/replenishment/{plan_id}/approve', response_model=ReplenishmentPlanRead)
def approve_replenishment_plan(
    plan_id: str,
    payload: ReplenishmentApproveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='Admin role required')
    plan = organization_scoped_get(
        db,
        ReplenishmentPlan,
        plan_id,
        writable.organization_id if writable else actor_organization_id(user, db),
        not_found_detail='Plan not found',
    )
    if plan.status != ReplenishmentPlanStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail='Only pending plans can be approved')

    plan.status = ReplenishmentPlanStatus.APPROVED
    plan.approved_quantity = payload.approved_quantity or plan.suggested_quantity
    plan.approved_by_user_id = user.id
    plan.approved_at = datetime.now(UTC)
    plan.rejection_reason = None
    if payload.note:
        plan.rationale = f'{plan.rationale}. Approval note: {payload.note}'
    db.add(plan)

    record_audit_event(
        db,
        event_type='planning.replenishment_approved',
        entity_type='replenishment_plan',
        entity_id=plan.id,
        actor=user,
        organization_id=resolve_actor_organization_id(db, user),
        description=f'Approved replenishment plan for {plan.id}',
        payload={'approved_quantity': plan.approved_quantity, 'note': payload.note},
    )
    db.commit()
    db.refresh(plan)

    warehouse = db.get(Warehouse, plan.warehouse_id)
    item = db.get(Item, plan.item_id)
    return _to_read(plan, warehouse.code if warehouse else 'unknown', item.sku if item else 'unknown')


@router.post('/replenishment/{plan_id}/reject', response_model=ReplenishmentPlanRead)
def reject_replenishment_plan(
    plan_id: str,
    payload: ReplenishmentRejectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):

    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='Admin role required')
    plan = organization_scoped_get(
        db,
        ReplenishmentPlan,
        plan_id,
        writable.organization_id if writable else actor_organization_id(user, db),
        not_found_detail='Plan not found',
    )
    if plan.status != ReplenishmentPlanStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail='Only pending plans can be rejected')

    plan.status = ReplenishmentPlanStatus.REJECTED
    plan.rejection_reason = payload.reason
    plan.approved_by_user_id = user.id
    plan.approved_at = datetime.now(UTC)
    db.add(plan)

    record_audit_event(
        db,
        event_type='planning.replenishment_rejected',
        entity_type='replenishment_plan',
        entity_id=plan.id,
        actor=user,
        organization_id=resolve_actor_organization_id(db, user),
        description=f'Rejected replenishment plan for {plan.id}',
        payload={'reason': payload.reason},
    )
    db.commit()
    db.refresh(plan)

    warehouse = db.get(Warehouse, plan.warehouse_id)
    item = db.get(Item, plan.item_id)
    return _to_read(plan, warehouse.code if warehouse else 'unknown', item.sku if item else 'unknown')
