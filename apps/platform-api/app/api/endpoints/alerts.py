from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.alert import Alert
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.shipment import Shipment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.alert import AlertAction, AlertCreate, AlertRead, AlertSeverity, AlertStatus, AlertType
from app.schemas.auth import UserRole
from app.services.audit import record_audit_event, resolve_actor_organization_id

router = APIRouter()


@router.get('', response_model=list[AlertRead])
def list_alerts(
    status: AlertStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    stmt = select(Alert).order_by(asc(Alert.created_at))
    if status:
        stmt = stmt.where(Alert.status == status)
    return db.execute(stmt).scalars().all()


@router.post('', response_model=AlertRead, status_code=201)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    alert = Alert(
        alert_type=payload.alert_type,
        severity=payload.severity,
        status=AlertStatus.OPEN,
        title=payload.title,
        message=payload.message,
        related_entity_type=payload.related_entity_type,
        related_entity_id=payload.related_entity_id,
    )
    db.add(alert)

    record_audit_event(
        db,
        event_type='alert.created',
        entity_type='alert',
        entity_id=alert.id,
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Created alert {alert.title}',
        payload={'alert_type': alert.alert_type, 'severity': alert.severity},
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.post('/scan', response_model=list[AlertRead])
def scan_alerts(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    generated: list[Alert] = []

    low_stock_rows = db.execute(
        select(Inventory, Warehouse.code, Item.sku)
        .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
        .join(Item, Item.id == Inventory.item_id)
    ).all()
    for row in low_stock_rows:
        if row.Inventory.quantity_on_hand >= row.Inventory.safety_stock:
            continue
        related_id = f'{row.code}:{row.sku}'
        exists = db.execute(
            select(Alert).where(
                Alert.alert_type == AlertType.LOW_STOCK,
                Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
                Alert.related_entity_type == 'inventory',
                Alert.related_entity_id == related_id,
            )
        ).scalar_one_or_none()
        if exists:
            continue
        generated.append(
            Alert(
                alert_type=AlertType.LOW_STOCK,
                severity=AlertSeverity.HIGH,
                status=AlertStatus.OPEN,
                title=f'Low stock at {row.code}',
                message=f'SKU {row.sku} below safety stock ({row.Inventory.quantity_on_hand} < {row.Inventory.safety_stock})',
                related_entity_type='inventory',
                related_entity_id=related_id,
            )
        )

    delayed_shipments = db.execute(select(Shipment).where(Shipment.status == 'delayed')).scalars().all()
    for shipment in delayed_shipments:
        exists = db.execute(
            select(Alert).where(
                Alert.alert_type == AlertType.DELAYED_SHIPMENT,
                Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
                Alert.related_entity_type == 'shipment',
                Alert.related_entity_id == shipment.id,
            )
        ).scalar_one_or_none()
        if exists:
            continue
        generated.append(
            Alert(
                alert_type=AlertType.DELAYED_SHIPMENT,
                severity=AlertSeverity.CRITICAL,
                status=AlertStatus.OPEN,
                title=f'Delayed shipment: {shipment.shipment_no}',
                message=shipment.delay_reason or 'Shipment is delayed',
                related_entity_type='shipment',
                related_entity_id=shipment.id,
            )
        )

    for alert in generated:
        db.add(alert)

    record_audit_event(
        db,
        event_type='alert.scan_generated',
        entity_type='alert_scan',
        actor=actor,
        organization_id=resolve_actor_organization_id(db, actor),
        description=f'Generated {len(generated)} alerts from exception scan',
        payload={'generated_count': len(generated)},
    )

    db.commit()
    for alert in generated:
        db.refresh(alert)
    return generated


@router.post('/{alert_id}/acknowledge', response_model=AlertRead)
def acknowledge_alert(
    alert_id: str,
    payload: AlertAction,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in {UserRole.OPERATOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail='Insufficient role')
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail='Alert not found')
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(status_code=400, detail='Cannot acknowledge a resolved alert')

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by_user_id = user.id
    alert.acknowledged_at = datetime.now(UTC)
    if payload.note:
        alert.resolution_note = payload.note
    db.add(alert)

    record_audit_event(
        db,
        event_type='alert.acknowledged',
        entity_type='alert',
        entity_id=alert.id,
        actor=user,
        description=f'Acknowledged alert {alert.title}',
        payload={'status': alert.status, 'note': payload.note},
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.post('/{alert_id}/resolve', response_model=AlertRead)
def resolve_alert(
    alert_id: str,
    payload: AlertAction,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in {UserRole.OPERATOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail='Insufficient role')
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail='Alert not found')

    alert.status = AlertStatus.RESOLVED
    if not alert.acknowledged_by_user_id:
        alert.acknowledged_by_user_id = user.id
        alert.acknowledged_at = datetime.now(UTC)
    alert.resolved_by_user_id = user.id
    alert.resolved_at = datetime.now(UTC)
    if payload.note:
        alert.resolution_note = payload.note
    db.add(alert)

    record_audit_event(
        db,
        event_type='alert.resolved',
        entity_type='alert',
        entity_id=alert.id,
        actor=user,
        description=f'Resolved alert {alert.title}',
        payload={'status': alert.status, 'note': payload.note},
    )
    db.commit()
    db.refresh(alert)
    return alert
