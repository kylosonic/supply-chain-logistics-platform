from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
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
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.route import RouteSchedule
from app.models.shipment import Shipment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.alert import AlertAction, AlertCreate, AlertRead, AlertSeverity, AlertStatus, AlertType
from app.schemas.auth import UserRole
from app.services.audit import record_audit_event
from app.services.rerouting import generate_rerouting_plan

router = APIRouter()


@router.get('', response_model=list[AlertRead])
def list_alerts(
    status: AlertStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # alerts are tenant data.
    organization_id = membership.organization_id
    stmt = scoped_to_organization(select(Alert), Alert, organization_id)
    if status:
        stmt = stmt.where(Alert.status == status)
    return db.execute(stmt.order_by(asc(Alert.created_at))).scalars().all()


@router.post('', response_model=AlertRead, status_code=201)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(actor, writable)

    alert = Alert(
        organization_id=organization_id,
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
        organization_id=str(organization_id),
        description=f'Created alert {alert.title}',
        payload={'alert_type': alert.alert_type, 'severity': alert.severity},
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.post('/scan', response_model=list[AlertRead])
def scan_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    # a scan must only ever generate alerts from the caller's own
    # inventory and shipments, and stamp them with the caller's org.
    organization_id = resolve_scoped_organization(actor, writable)
    generated: list[Alert] = []

    inventory_stmt = (
        select(Inventory, Warehouse.code, Item.sku)
        .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
        .join(Item, Item.id == Inventory.item_id)
    )
    low_stock_rows = db.execute(
        scoped_to_organization(inventory_stmt, Inventory, organization_id)
    ).all()
    for row in low_stock_rows:
        if row.Inventory.quantity_on_hand >= row.Inventory.safety_stock:
            continue
        related_id = f'{row.code}:{row.sku}'
        exists_stmt = select(Alert).where(
            Alert.alert_type == AlertType.LOW_STOCK,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
            Alert.related_entity_type == 'inventory',
            Alert.related_entity_id == related_id,
        )
        exists = db.execute(
            order_by_organization_first(
                scoped_to_organization(exists_stmt, Alert, organization_id), Alert
            )
        ).scalars().first()
        if exists:
            continue
        generated.append(
            Alert(
                organization_id=organization_id,
                alert_type=AlertType.LOW_STOCK,
                severity=AlertSeverity.HIGH,
                status=AlertStatus.OPEN,
                title=f'Low stock at {row.code}',
                message=(
                    f'SKU {row.sku} below safety stock '
                    f'({row.Inventory.quantity_on_hand} < {row.Inventory.safety_stock})'
                ),
                related_entity_type='inventory',
                related_entity_id=related_id,
            )
        )

    delayed_stmt = scoped_to_organization(
        select(Shipment).where(Shipment.status == 'delayed'), Shipment, organization_id
    )
    delayed_shipments = db.execute(delayed_stmt).scalars().all()
    now = datetime.now(UTC)
    tasks_to_queue = []
    
    for shipment in delayed_shipments:
        exists = db.execute(
            order_by_organization_first(
                scoped_to_organization(
                    select(Alert).where(
                        Alert.alert_type == AlertType.DELAYED_SHIPMENT,
                        Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
                        Alert.related_entity_type == 'shipment',
                        Alert.related_entity_id == shipment.id,
                    ),
                    Alert,
                    organization_id,
                ),
                Alert,
            )
        ).scalars().first()
        if exists:
            continue
            
        alert = Alert(
            organization_id=organization_id,
            alert_type=AlertType.DELAYED_SHIPMENT,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
            title=f'Delayed shipment: {shipment.shipment_no}',
            message=shipment.delay_reason or 'Shipment is delayed',
            related_entity_type='shipment',
            related_entity_id=shipment.id,
        )
        generated.append(alert)
        
        if shipment.expected_delivery:
            delay = now - shipment.expected_delivery
            if delay.total_seconds() > 30 * 60:
                tasks_to_queue.append((alert, shipment.id))

    for alert in generated:
        db.add(alert)

    record_audit_event(
        db,
        event_type='alert.scan_generated',
        entity_type='alert_scan',
        actor=actor,
        organization_id=str(organization_id),
        description=f'Generated {len(generated)} alerts from exception scan',
        payload={'generated_count': len(generated)},
    )

    db.commit()
    for alert in generated:
        db.refresh(alert)
        
    for alert, shipment_id in tasks_to_queue:
        background_tasks.add_task(generate_rerouting_plan, db, alert.id, shipment_id)
        
    return generated


@router.post('/{alert_id}/acknowledge', response_model=AlertRead)
def acknowledge_alert(
    alert_id: str,
    payload: AlertAction,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(user, writable)
    alert = organization_scoped_get(
        db,
        Alert,
        alert_id,
        organization_id,
        not_found_detail='Alert not found',
        include_legacy_null=False,
    )
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
        organization_id=str(organization_id),
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
    user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(user, writable)
    alert = organization_scoped_get(
        db,
        Alert,
        alert_id,
        organization_id,
        not_found_detail='Alert not found',
        include_legacy_null=False,
    )

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
        organization_id=str(organization_id),
        description=f'Resolved alert {alert.title}',
        payload={'status': alert.status, 'note': payload.note},
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.post('/{alert_id}/auto-resolve', response_model=AlertRead)
def auto_resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(user, writable)
    alert = organization_scoped_get(
        db,
        Alert,
        alert_id,
        organization_id,
        not_found_detail='Alert not found',
        include_legacy_null=False,
    )

    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(status_code=400, detail='Alert already resolved')
        
    if not alert.payload or 'rerouting_plan' not in alert.payload:
        raise HTTPException(status_code=400, detail='No auto-resolve plan available')

    plan = alert.payload['rerouting_plan']
    if not isinstance(plan, dict):
        raise HTTPException(status_code=422, detail='Saved rerouting candidate is invalid')
    
    if alert.related_entity_type == 'shipment' and alert.related_entity_id:
        shipment = organization_scoped_get(
            db,
            Shipment,
            alert.related_entity_id,
            organization_id,
            not_found_detail='Shipment not found',
            include_legacy_null=False,
        )
        try:
            proposed_route_id = UUID(str(plan.get('proposed_route_id')))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail='Saved rerouting candidate is invalid') from None
        route = organization_scoped_get(
            db,
            RouteSchedule,
            proposed_route_id,
            organization_id,
            not_found_detail='Rerouting candidate not found',
            include_legacy_null=False,
        )
        shipment.route_schedule_id = route.id
        shipment.status = 'in_transit'
        shipment.delay_reason = None
        db.add(shipment)
            
    alert.status = AlertStatus.RESOLVED
    alert.resolved_by_user_id = user.id
    alert.resolved_at = datetime.now(UTC)
    route_name = plan.get('route_name') or 'saved schedule'
    alert.resolution_note = f'Auto-resolved with saved schedule {route_name}.'
    db.add(alert)
    
    record_audit_event(
        db,
        event_type='alert.auto_resolved',
        entity_type='alert',
        entity_id=alert.id,
        actor=user,
        organization_id=str(organization_id),
        description=f'Auto-resolved alert {alert.title}',
        payload={'status': alert.status, 'note': alert.resolution_note, 'plan': plan},
    )
    db.commit()
    db.refresh(alert)
    return alert
