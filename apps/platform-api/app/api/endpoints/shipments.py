from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.db.session import get_db
from app.models.alert import Alert
from app.models.item import Item
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
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    shipments = db.execute(select(Shipment).order_by(asc(Shipment.created_at))).scalars().all()
    return [_shipment_to_read(db, shipment) for shipment in shipments]


@router.post('', response_model=ShipmentRead, status_code=201)
def create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    existing = db.execute(select(Shipment).where(Shipment.shipment_no == payload.shipment_no)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail='Shipment number already exists')

    origin = db.execute(select(Warehouse).where(Warehouse.code == payload.origin_warehouse_code)).scalar_one_or_none()
    if not origin:
        raise HTTPException(status_code=404, detail='Origin warehouse code not found')

    destination = db.execute(
        select(Warehouse).where(Warehouse.code == payload.destination_warehouse_code)
    ).scalar_one_or_none()
    if not destination:
        raise HTTPException(status_code=404, detail='Destination warehouse code not found')

    item = db.execute(select(Item).where(Item.sku == payload.sku)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    if payload.route_schedule_id:
        route = db.get(RouteSchedule, payload.route_schedule_id)
        if not route:
            raise HTTPException(status_code=404, detail='Route schedule not found')

    shipment = Shipment(
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
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail='Shipment not found')
    return _shipment_to_read(db, shipment)


@router.post('/{shipment_id}/status', response_model=ShipmentRead)
def update_shipment_status(
    shipment_id: str,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail='Shipment not found')

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
