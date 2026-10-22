from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.security import (
    get_current_membership,
    order_by_organization_first,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.route import RouteSchedule
from app.models.shipment import Shipment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.alert import AlertSeverity, AlertStatus, AlertType
from app.schemas.auth import UserRole
from app.schemas.shipment import (
    ShipmentAssignDriver,
    ShipmentCreate,
    ShipmentRead,
    ShipmentStatus,
    ShipmentStatusUpdate,
)
from app.services import cash_ledger
from app.services.audit import record_audit_event

router = APIRouter()


def _shipment_to_read(db: Session, shipment: Shipment) -> ShipmentRead:
    origin = db.get(Warehouse, shipment.origin_warehouse_id)
    destination = db.get(Warehouse, shipment.destination_warehouse_id)
    item = db.get(Item, shipment.item_id)
    driver = db.get(Driver, shipment.driver_id) if shipment.driver_id else None
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
        driver_id=shipment.driver_id,
        driver_name=driver.full_name if driver else None,
        cod_amount_etb=shipment.cod_amount_etb or 0,
        client_ref=shipment.client_ref,
    )


@router.get('', response_model=list[ShipmentRead])
def list_shipments(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64 (audit H-1): shipments are tenant data. An org-scoped actor sees
    # their own rows plus explicitly legacy rows; business access requires an
    # active organization membership, so an org-less actor is denied upstream.
    organization_id = membership.organization_id
    stmt = scoped_to_organization(select(Shipment), Shipment, organization_id)
    shipments = db.execute(stmt.order_by(asc(Shipment.created_at))).scalars().all()
    return [_shipment_to_read(db, shipment) for shipment in shipments]


@router.post('', response_model=ShipmentRead, status_code=201)
def create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(actor, writable)

    # NB-86 idempotency: a create replayed over a dropped mobile connection must
    # return the shipment it already made, not a second one (which would also open
    # a second cash record). The client supplies a stable reference; the partial
    # unique index on (organization_id, client_ref) is the real guard, and this
    # lookup is the fast path that avoids a 500 on the constraint violation.
    if payload.client_ref:
        replay_stmt = select(Shipment).where(Shipment.client_ref == payload.client_ref)
        if organization_id is not None:
            replay_stmt = replay_stmt.where(Shipment.organization_id == organization_id)
        replayed = db.execute(replay_stmt).scalars().first()
        if replayed is not None:
            return _shipment_to_read(db, replayed)

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

    # NB-86: an assigned driver must belong to the caller's tenant. Without this
    # check a caller could assign another company's driver by id, leaking the
    # existence of that row and misattributing the cash that follows it.
    if payload.driver_id:
        driver = organization_scoped_get(
            db,
            Driver,
            payload.driver_id,
            organization_id,
            not_found_detail='Driver not found',
        )
        if driver.status != 'active':
            raise HTTPException(status_code=409, detail='That driver is not active')

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
        driver_id=payload.driver_id,
        cod_amount_etb=payload.cod_amount_etb,
        client_ref=payload.client_ref,
        scope_3_emissions_kg=payload.scope_3_emissions_kg,
    )
    db.add(shipment)

    record_audit_event(
        db,
        event_type='shipment.created',
        entity_type='shipment',
        entity_id=shipment.id,
        actor=actor,
        organization_id=str(organization_id),
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
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    shipment = organization_scoped_get(
        db,
        Shipment,
        shipment_id,
        membership.organization_id,
        not_found_detail='Shipment not found',
        include_legacy_null=False,
    )
    return _shipment_to_read(db, shipment)


@router.post('/{shipment_id}/status', response_model=ShipmentRead)
def update_shipment_status(
    shipment_id: str,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(actor, writable)
    shipment = organization_scoped_get(
        db,
        Shipment,
        shipment_id,
        organization_id,
        not_found_detail='Shipment not found',
        include_legacy_null=False,
    )

    if payload.status == ShipmentStatus.DELAYED and not payload.delay_reason:
        raise HTTPException(
            status_code=400,
            detail='delay_reason is required when marking a shipment delayed',
        )

    if payload.cash_collected_etb is not None and payload.status != ShipmentStatus.DELIVERED:
        raise HTTPException(
            status_code=400,
            detail='cash_collected_etb is only accepted when marking a shipment delivered',
        )
    if payload.cash_collected_etb is not None:
        expected_cash = shipment.cod_amount_etb or 0
        if payload.cash_collected_etb > expected_cash:
            raise HTTPException(
                status_code=422,
                detail='Collected cash cannot exceed the cash-on-delivery amount',
            )
        if payload.cash_collected_etb < expected_cash and not (payload.cash_note or '').strip():
            raise HTTPException(
                status_code=422,
                detail='A cash note is required when collecting less than the expected amount',
            )

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

    # NB-86: a delivery is where cash actually changes hands, so the cash record is
    # opened here rather than in a second call the driver might never complete.
    # Opening is idempotent (one row per shipment), which is what makes a replayed
    # confirmation safe over an unreliable connection.
    cash_record = None
    if payload.status == ShipmentStatus.DELIVERED and (shipment.cod_amount_etb or 0) > 0:
        cash_record = cash_ledger.open_for_shipment(
            db,
            shipment,
            collected=payload.cash_collected_etb,
            note=payload.cash_note,
        )

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
        organization_id=str(organization_id),
        description=f'Updated shipment {shipment.shipment_no} to {payload.status}',
        payload={
            'from_status': previous_status,
            'to_status': payload.status,
            'delay_reason': payload.delay_reason,
            'cash_collected_etb': (
                str(payload.cash_collected_etb)
                if payload.cash_collected_etb is not None
                else None
            ),
            'cash_shortfall_etb': str(cash_record.shortfall_etb) if cash_record else None,
        },
    )
    db.commit()
    db.refresh(shipment)
    return _shipment_to_read(db, shipment)


@router.post('/{shipment_id}/driver', response_model=ShipmentRead)
def assign_shipment_driver(
    shipment_id: str,
    payload: ShipmentAssignDriver,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    """Assign or clear the driver on a shipment.

    Kept separate from the status endpoint because assignment happens during
    dispatch, before any movement, and is the single most frequent edit an
    operator makes in a morning.
    """
    organization_id = resolve_scoped_organization(actor, writable)
    shipment = organization_scoped_get(
        db,
        Shipment,
        shipment_id,
        organization_id,
        not_found_detail='Shipment not found',
        include_legacy_null=False,
    )

    previous_driver_id = shipment.driver_id
    driver_name = None
    if payload.driver_id is None:
        shipment.driver_id = None
    else:
        driver = organization_scoped_get(
            db,
            Driver,
            payload.driver_id,
            organization_id,
            not_found_detail='Driver not found',
        )
        if driver.status != 'active':
            raise HTTPException(status_code=409, detail='That driver is not active')
        shipment.driver_id = driver.id
        driver_name = driver.full_name

    db.add(shipment)

    # Keep the cash record's driver in step: if cash is already outstanding, the
    # person accountable for it must follow the reassignment, otherwise the ledger
    # points at whoever happened to be assigned when the row was opened.
    cash_record = cash_ledger.get_by_shipment(db, shipment.id)
    if cash_record is not None and cash_record.status not in ('settled', 'voided'):
        cash_record.driver_id = shipment.driver_id
        db.add(cash_record)

    record_audit_event(
        db,
        event_type='shipment.driver_assigned',
        entity_type='shipment',
        entity_id=shipment.id,
        actor=actor,
        organization_id=str(organization_id),
        description=(
            f'Assigned {driver_name} to shipment {shipment.shipment_no}'
            if driver_name
            else f'Cleared driver on shipment {shipment.shipment_no}'
        ),
        payload={
            'from_driver_id': str(previous_driver_id) if previous_driver_id else None,
            'to_driver_id': str(shipment.driver_id) if shipment.driver_id else None,
        },
    )
    db.commit()
    db.refresh(shipment)
    return _shipment_to_read(db, shipment)
