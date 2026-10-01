from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.driver import Driver
from app.models.membership import OrganizationMembership
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.shipment import (
    DriverCreate,
    DriverRead,
    DriverShipmentRead,
    DriverStatus,
    DriverUpdate,
    ShipmentStatus,
)
from app.services.audit import record_audit_event, resolve_actor_organization_id

router = APIRouter()


def _driver_to_read(driver: Driver) -> DriverRead:
    return DriverRead(
        id=driver.id,
        created_at=driver.created_at,
        full_name=driver.full_name,
        phone=driver.phone,
        license_no=driver.license_no,
        vehicle_plate=driver.vehicle_plate,
        status=DriverStatus(driver.status),
        notes=driver.notes,
    )


@router.get('', response_model=list[DriverRead])
def list_drivers(
    status: DriverStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN, UserRole.VIEWER)),
):
    """The roster. This is the list an operator reads out when a truck is late."""
    stmt = scoped_to_organization(
        select(Driver), Driver, actor_organization_id(actor, db)
    ).order_by(Driver.full_name.asc())
    if status is not None:
        stmt = stmt.where(Driver.status == status)
    return [_driver_to_read(d) for d in db.execute(stmt).scalars().all()]


@router.post('', response_model=DriverRead, status_code=201)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(actor, writable)
    if organization_id is None:
        raise HTTPException(status_code=400, detail='A workspace is required to add a driver')

    driver = Driver(
        organization_id=organization_id,
        full_name=payload.full_name,
        phone=payload.phone,
        license_no=payload.license_no,
        vehicle_plate=payload.vehicle_plate,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(driver)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        # Phone is the natural key within a tenant; a duplicate is a real
        # conflict the operator must resolve, not a server error.
        raise HTTPException(
            status_code=409, detail='A driver with that phone number already exists'
        ) from None

    record_audit_event(
        db,
        event_type='driver.created',
        entity_type='driver',
        entity_id=driver.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Added driver {driver.full_name}',
        payload={'phone': driver.phone, 'vehicle_plate': driver.vehicle_plate},
    )
    db.commit()
    db.refresh(driver)
    return _driver_to_read(driver)


@router.get('/{driver_id}', response_model=DriverRead)
def get_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN, UserRole.VIEWER)),
):
    driver = organization_scoped_get(
        db, Driver, driver_id, actor_organization_id(actor, db), not_found_detail='Driver not found'
    )
    return _driver_to_read(driver)


@router.patch('/{driver_id}', response_model=DriverRead)
def update_driver(
    driver_id: str,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    driver = organization_scoped_get(
        db,
        Driver,
        driver_id,
        resolve_scoped_organization(actor, writable),
        not_found_detail='Driver not found',
    )

    changed: dict[str, object] = {}
    for field in ('full_name', 'phone', 'license_no', 'vehicle_plate', 'status', 'notes'):
        value = getattr(payload, field)
        if value is not None:
            # DriverStatus is a StrEnum, so it stores as its plain string value.
            setattr(driver, field, str(value) if field == 'status' else value)
            changed[field] = str(value) if field == 'status' else value

    if not changed:
        return _driver_to_read(driver)

    db.add(driver)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail='A driver with that phone number already exists'
        ) from None

    record_audit_event(
        db,
        event_type='driver.updated',
        entity_type='driver',
        entity_id=driver.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Updated driver {driver.full_name}',
        payload={k: str(v) for k, v in changed.items()},
    )
    db.commit()
    db.refresh(driver)
    return _driver_to_read(driver)


@router.get('/{driver_id}/shipments', response_model=list[DriverShipmentRead])
def list_driver_shipments(
    driver_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN, UserRole.VIEWER)),
):
    """What this driver is currently carrying.

    Answers the operator's actual question — "what has Yohannes got on the van
    right now?" — without reading the whole shipment table.
    """
    organization_id = actor_organization_id(actor, db)
    driver = organization_scoped_get(
        db, Driver, driver_id, organization_id, not_found_detail='Driver not found'
    )
    stmt = (
        scoped_to_organization(
            select(Shipment).where(Shipment.driver_id == driver.id), Shipment, organization_id
        )
        .order_by(Shipment.expected_delivery.asc().nullslast())
        .limit(limit)
    )
    return [
        DriverShipmentRead(
            id=s.id,
            created_at=s.created_at,
            shipment_no=s.shipment_no,
            status=ShipmentStatus(s.status),
            expected_delivery=s.expected_delivery,
            cod_amount_etb=s.cod_amount_etb or 0,
        )
        for s in db.execute(stmt).scalars().all()
    ]


@router.delete('/{driver_id}', status_code=204)
def deactivate_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    """Deactivate rather than delete.

    A hard delete is refused because shipments reference the driver: history must
    survive a roster cleanup, and the FK is SET NULL only as a last resort, not as
    the normal path.
    """
    driver = organization_scoped_get(
        db,
        Driver,
        driver_id,
        resolve_scoped_organization(actor, writable),
        not_found_detail='Driver not found',
    )
    driver.status = 'inactive'
    db.add(driver)

    record_audit_event(
        db,
        event_type='driver.deactivated',
        entity_type='driver',
        entity_id=driver.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Deactivated driver {driver.full_name}',
        payload={},
    )
    db.commit()
