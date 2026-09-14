from __future__ import annotations

from datetime import timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select, text
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
from app.core.config import settings
from app.core.observability import app_metrics
from app.db.session import get_db
from app.models.alert import Alert
from app.models.audit_event import AuditEvent
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.replenishment import ReplenishmentPlan
from app.models.route_history import RouteOptimizationRun
from app.models.shipment import Shipment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.dock_appointment import DockAppointment
from app.schemas.auth import UserRole
from app.schemas.dock_appointment import DockAppointmentPayload, DockAppointmentResponse
from app.schemas.ops_insights import AuditEventRead, ExceptionFeedItem, ExceptionFeedResponse, ExceptionFeedSummary

router = APIRouter()


@router.get('/ready')
def readiness(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text('SELECT 1'))
    except Exception as exc:
        raise HTTPException(status_code=503, detail='Database unavailable') from exc
    return {'status': 'ok', 'env': settings.app_env}


@router.get('/metrics')
def metrics(_: User = Depends(require_roles(UserRole.ADMIN))) -> dict:
    return app_metrics.snapshot()


@router.get('/audit-timeline', response_model=list[AuditEventRead])
def audit_timeline(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64 (audit H-1): the audit trail holds operator emails and phone-masked
    # payloads, so it must never leak across tenants.
    stmt = scoped_to_organization(select(AuditEvent), AuditEvent, actor_organization_id(actor, db))
    rows = db.execute(stmt.order_by(desc(AuditEvent.created_at)).limit(limit)).scalars().all()
    return rows


@router.get('/exception-feed', response_model=ExceptionFeedResponse)
def exception_feed(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    organization_id = actor_organization_id(actor, db)

    alert_stmt = scoped_to_organization(
        select(Alert).where(Alert.status.in_(['open', 'acknowledged'])), Alert, organization_id
    )
    alerts = db.execute(
        alert_stmt.order_by(desc(Alert.created_at)).limit(limit)
    ).scalars().all()

    plan_stmt = scoped_to_organization(
        select(ReplenishmentPlan, Warehouse.code, Item.sku)
        .join(Warehouse, Warehouse.id == ReplenishmentPlan.warehouse_id)
        .join(Item, Item.id == ReplenishmentPlan.item_id)
        .where(ReplenishmentPlan.status == 'pending_approval'),
        ReplenishmentPlan,
        organization_id,
    )
    pending_plans = db.execute(
        plan_stmt.order_by(desc(ReplenishmentPlan.created_at)).limit(limit)
    ).all()

    run_stmt = scoped_to_organization(
        select(RouteOptimizationRun).where(RouteOptimizationRun.unassigned_count > 0),
        RouteOptimizationRun,
        organization_id,
    )
    route_runs = db.execute(
        run_stmt.order_by(desc(RouteOptimizationRun.created_at)).limit(limit)
    ).scalars().all()

    items: list[ExceptionFeedItem] = [
        ExceptionFeedItem(
            source_type='alert',
            source_id=alert.id,
            severity=alert.severity,
            status=alert.status,
            title=alert.title,
            message=alert.message,
            entity_type=alert.related_entity_type,
            entity_id=alert.related_entity_id,
            created_at=alert.created_at,
            metadata={'alert_type': alert.alert_type},
        )
        for alert in alerts
    ]

    items.extend(
        ExceptionFeedItem(
            source_type='replenishment_plan',
            source_id=row.ReplenishmentPlan.id,
            severity='high',
            status=row.ReplenishmentPlan.status,
            title=f'Pending replenishment approval for {row.sku}',
            message=row.ReplenishmentPlan.rationale,
            entity_type='replenishment_plan',
            entity_id=row.ReplenishmentPlan.id,
            created_at=row.ReplenishmentPlan.created_at,
            metadata={
                'warehouse_code': row.code,
                'sku': row.sku,
                'suggested_quantity': row.ReplenishmentPlan.suggested_quantity,
            },
        )
        for row in pending_plans
    )

    items.extend(
        ExceptionFeedItem(
            source_type='route_optimization_run',
            source_id=run.id,
            severity='medium' if run.unassigned_count == 1 else 'high',
            status='requires_review',
            title=f'Route run {run.route_name} left deliveries unassigned',
            message=f'{run.unassigned_count} deliver{"" if run.unassigned_count == 1 else "ies"} need manual review.',
            entity_type='route_optimization_run',
            entity_id=run.id,
            created_at=run.created_at,
            metadata={
                'schedule_date': str(run.schedule_date),
                'unassigned_count': run.unassigned_count,
                'persist_requested': run.persist_requested,
            },
        )
        for run in route_runs
    )

    items.sort(key=lambda item: item.created_at, reverse=True)

    delayed_stmt = scoped_to_organization(
        select(Shipment).where(Shipment.status == 'delayed'), Shipment, organization_id
    )
    delayed_shipments = db.execute(delayed_stmt).scalars().all()

    return ExceptionFeedResponse(
        summary=ExceptionFeedSummary(
            open_alerts=len(alerts),
            delayed_shipments=len(delayed_shipments),
            pending_replenishment_plans=len(pending_plans),
            route_runs_with_unassigned_deliveries=len(route_runs),
        ),
        items=items[:limit],
    )


@router.post('/live-eta', response_model=DockAppointmentResponse)
def update_live_eta(
    payload: DockAppointmentPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    organization_id = resolve_scoped_organization(actor, writable)

    # NB-64: the warehouse being updated must belong to the caller's tenant,
    # otherwise an operator could rewrite another company's dock schedule.
    warehouse = organization_scoped_get(
        db,
        Warehouse,
        payload.warehouse_id,
        organization_id,
        not_found_detail='Warehouse not found',
    )

    appointment_stmt = order_by_organization_first(
        scoped_to_organization(
            select(DockAppointment).where(
                DockAppointment.warehouse_id == warehouse.id,
                DockAppointment.truck_id == payload.truck_id,
                DockAppointment.status.in_(['scheduled', 'rescheduled']),
            ),
            DockAppointment,
            organization_id,
        ),
        DockAppointment,
    )
    appointment = db.execute(appointment_stmt).scalars().first()

    if not appointment:
        appointment = DockAppointment(
            organization_id=organization_id or warehouse.organization_id,
            warehouse_id=warehouse.id,
            truck_id=payload.truck_id,
            status='scheduled',
            scheduled_time=payload.expected_time,
            expected_time=payload.expected_time,
        )
        db.add(appointment)
    else:
        appointment.expected_time = payload.expected_time
        
        time_slip = payload.expected_time - appointment.scheduled_time
        if time_slip > timedelta(minutes=45):
            appointment.scheduled_time = payload.expected_time
            appointment.status = 'rescheduled'

        db.add(appointment)
        
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get('/dock-appointments', response_model=list[DockAppointmentResponse])
def get_dock_appointments(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    stmt = scoped_to_organization(
        select(DockAppointment), DockAppointment, actor_organization_id(actor, db)
    )
    rows = db.execute(stmt.order_by(DockAppointment.scheduled_time)).scalars().all()
    return rows
