from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    order_by_organization_first,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.alert import Alert
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.route import RouteSchedule
from app.models.shipment import Shipment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.alert import AlertSeverity, AlertStatus, AlertType
from app.schemas.auth import UserRole
from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentStatus, ShipmentStatusUpdate
from app.services.audit import record_audit_event, resolve_actor_organization_id

router = APIRouter()


def _shipment_to_read(db: Session, shipment: Shipment) -> ShipmentRead:
    origin = db.get(Warehouse, shipment.origin_warehouse_id)
    destination = db.get(Warehouse, shipment.destination_warehouse_id)
    item = db.get(Item, shipment.item_id)
    return ShipmentRead(
        id=shipment.id,
        created_at=shipment.created_at,
        shipment_no=shipment.shipment_no,
        route_schedule_id=shipment.route_schedule_id,
        origin_warehouse_code=origin.code if origin else 'unknown',
        destination_warehouse_code=destination.code if destination else 'unknown',
        sku=item.sku if item else 'unknown',
        quantity_units=shipment.quantity_units,
        planned_departure=shipment.planned_departure,
        expected_delivery=shipment.expected_delivery,
        actual_delivery=shipment.actual_delivery,
        status=ShipmentStatus(shipment.status),
        last_known_location=shipment.last_known_location,
        delay_reason=shipment.delay_reason,
        proof_of_delivery_ref=shipment.proof_of_delivery_ref,
        scope_3_emissions_kg=shipment.scope_3_emissions_kg,
    )


@router.get('', response_model=list[ShipmentRead])
def list_shipments(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64 (audit H-1): shipments are tenant data. An org-scoped actor sees
    # their own rows plus unattributed legacy rows; an org-less actor keeps the
    # pre-NB-64 pass-through behaviour.
    organization_id = actor_organization_id(actor, db)
    stmt = scoped_to_organization(select(Shipment), Shipment, organization_id)
    shipments = db.execute(stmt.order_by(asc(Shipment.created_at))).scalars().all()
    return [_shipment_to_read(db, shipment) for shipment in shipments]


@router.post('', response_model=ShipmentRead, status_code=201)
def create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(actor, writable)

    # Duplicate-number pre-check is equality-only per org (mirrors TECH-58):
    # a legacy unattributed row with the same number must not false-409 a
    # first create for a scoped org.
    exists_stmt = select(Shipment).where(Shipment.shipment_no == payload.shipment_no)
    if organization_id is not None:
        exists_stmt = exists_stmt.where(Shipment.organization_id == organization_id)
    existing = db.execute(exists_stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail='Shipment number already exists')

    # Referenced warehouses and items must belong to the caller's tenant.
    # Every lookup below prefers an own-org row over a same-code legacy
    # NULL-org row (seed data repeats codes across orgs), so ``first()`` is
    # used rather than ``scalar_one_or_none()`` which would raise on a tie.
    origin_stmt = order_by_organization_first(
        scoped_to_organization(
            select(Warehouse).where(Warehouse.code == payload.origin_warehouse_code),
            Warehouse,
            organization_id,
        ),
        Warehouse,
    )
    origin = db.execute(origin_stmt).scalars().first()
    if not origin:
        raise HTTPException(status_code=404, detail='Origin warehouse code not found')

    destination_stmt = order_by_organization_first(
        scoped_to_organization(
            select(Warehouse).where(Warehouse.code == payload.destination_warehouse_code),
            Warehouse,
            organization_id,
        ),
        Warehouse,
    )
    destination = db.execute(destination_stmt).scalars().first()
    if not destination:
        raise HTTPException(status_code=404, detail='Destination warehouse code not found')

    item_stmt = order_by_organization_first(
        scoped_to_organization(select(Item).where(Item.sku == payload.sku), Item, organization_id),
        Item,
    )
    item = db.execute(item_stmt).scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    if payload.route_schedule_id:
        route_stmt = order_by_organization_first(
            scoped_to_organization(
                select(RouteSchedule).where(RouteSchedule.id == payload.route_schedule_id),
                RouteSchedule,
                organization_id,
            ),
            RouteSchedule,
        )
        route = db.execute(route_stmt).scalars().first()
        if not route:
            raise HTTPException(status_code=404, detail='Route schedule not found')

    shipment = Shipment(
        organization_id=organization_id,
        shipment_no=payload.shipment_no,
        route_schedule_id=payload.route_schedule_id,
        origin_warehouse_id=origin.id,
        destination_warehouse_id=destination.id,
        item_id=item.id,
        quantity_units=payload.quantity_units,
        planned_departure=payload.planned_departure,
        expected_delivery=payload.expected_delivery,
        status=ShipmentStatus.PLANNED,
    )
    db.add(shipment)

    record_audit_event(
        db,
        event_type='shipment.created',
        entity_type='shipment',
        entity_id=shipment.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Created shipment {shipment.shipment_no}',
        payload={
            'origin_warehouse_code': payload.origin_warehouse_code,
            'destination_warehouse_code': payload.destination_warehouse_code,
            'sku': payload.sku,
            'quantity_units': payload.quantity_units,
        },
    )
    db.commit()
    db.refresh(shipment)
    return _shipment_to_read(db, shipment)


@router.get('/{shipment_id}', response_model=ShipmentRead)
def get_shipment(
    shipment_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    shipment = organization_scoped_get(
        db,
        Shipment,
        shipment_id,
        actor_organization_id(actor, db),
        not_found_detail='Shipment not found',
    )
    return _shipment_to_read(db, shipment)


@router.post('/{shipment_id}/status', response_model=ShipmentRead)
def update_shipment_status(
    shipment_id: str,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    shipment = organization_scoped_get(
        db,
        Shipment,
        shipment_id,
        resolve_scoped_organization(actor, writable),
        not_found_detail='Shipment not found',
    )

    if payload.status == ShipmentStatus.DELAYED and not payload.delay_reason:
        raise HTTPException(status_code=400, detail='delay_reason is required when marking a shipment delayed')

    previous_status = shipment.status
    shipment.status = payload.status
    if payload.last_known_location is not None:
        shipment.last_known_location = payload.last_known_location
    if payload.delay_reason is not None:
        shipment.delay_reason = payload.delay_reason
    if payload.proof_of_delivery_ref is not None:
        shipment.proof_of_delivery_ref = payload.proof_of_delivery_ref
    if payload.actual_delivery is not None:
        shipment.actual_delivery = payload.actual_delivery
    elif payload.status == ShipmentStatus.DELIVERED:
        shipment.actual_delivery = datetime.now(UTC)

    if payload.status == ShipmentStatus.DELAYED:
        existing_alert = db.execute(
            select(Alert).where(
                Alert.alert_type == AlertType.DELAYED_SHIPMENT,
                Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
                Alert.related_entity_type == 'shipment',
                Alert.related_entity_id == shipment.id,
            )
        ).scalar_one_or_none()
        if not existing_alert:
            db.add(
                Alert(
                    organization_id=shipment.organization_id,
                    alert_type=AlertType.DELAYED_SHIPMENT,
                    severity=AlertSeverity.HIGH,
                    status=AlertStatus.OPEN,
                    title=f'Shipment delayed: {shipment.shipment_no}',
                    message=payload.delay_reason or 'Shipment marked as delayed',
                    related_entity_type='shipment',
                    related_entity_id=shipment.id,
                )
            )

    db.add(shipment)

    record_audit_event(
        db,
        event_type='shipment.status_updated',
        entity_type='shipment',
        entity_id=shipment.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Updated shipment {shipment.shipment_no} to {payload.status}',
        payload={'from_status': previous_status, 'to_status': payload.status, 'delay_reason': payload.delay_reason},
    )
    db.commit()
    db.refresh(shipment)
    return _shipment_to_read(db, shipment)
