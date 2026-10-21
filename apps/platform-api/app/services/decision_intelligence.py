from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.dispatch import DeliveryOrder as DispatchDeliveryOrder
from app.models.driver import Driver
from app.models.inventory import Inventory
from app.models.route_history import RouteOptimizationRun
from app.models.shipment import Shipment
from app.models.warehouse import Warehouse

ZERO = Decimal('0.00')


def _age_hours(created_at: datetime, now: datetime) -> float:
    value = created_at.replace(tzinfo=UTC) if created_at.tzinfo is None else created_at.astimezone(UTC)
    return max(0.0, round((now - value).total_seconds() / 3600, 1))


def _severity_rank(value: str) -> int:
    return {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(value.lower(), 1)


def _suggested_action(alert: Alert) -> str:
    kind = alert.alert_type.lower()
    if 'delay' in kind or 'shipment' in kind:
        return (
            'Call the driver, confirm the delay reason, and decide whether to reassign '
            'or notify the customer.'
        )
    if 'stock' in kind or 'inventory' in kind:
        return 'Review the replenishment plan and confirm the next stock movement.'
    if 'temperature' in kind:
        return 'Inspect the shipment and document the excursion before releasing it.'
    if 'cash' in kind:
        return 'Review the driver cash declaration and the outstanding shortfall.'
    return 'Review the evidence and assign an owner before the next operating window.'


def exception_triage(db: Session, organization_id: UUID, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(UTC)
    alerts = db.execute(
        select(Alert)
        .where(
            Alert.organization_id == organization_id,
            Alert.status.in_(['open', 'acknowledged']),
        )
        .order_by(Alert.created_at.asc())
        .limit(50)
    ).scalars().all()
    rows = []
    for alert in alerts:
        age = _age_hours(alert.created_at, now)
        priority = min(100, _severity_rank(alert.severity) * 18 + min(int(age), 24))
        rows.append(
            {
                'alert_id': str(alert.id),
                'title': alert.title,
                'severity': alert.severity,
                'age_hours': age,
                'priority': priority,
                'suggested_action': _suggested_action(alert),
                'evidence': [
                    {'record_type': 'alert', 'record_id': str(alert.id), 'label': 'alert'},
                    {'record_type': 'age_hours', 'label': 'age', 'value': age},
                ],
            }
        )
    return sorted(rows, key=lambda row: int(row['priority']), reverse=True)[:10]


def cash_risk(db: Session, organization_id: UUID) -> list[dict]:
    rows = db.execute(
        select(
            DispatchDeliveryOrder.driver_id,
            Driver.full_name,
            func.count(DispatchDeliveryOrder.id).label('outstanding_count'),
            func.coalesce(func.sum(DispatchDeliveryOrder.cod_amount_etb), 0).label('expected'),
            func.coalesce(func.sum(DispatchDeliveryOrder.collected_cash_etb), 0).label('collected'),
        )
        .join(
            Driver,
            (Driver.id == DispatchDeliveryOrder.driver_id)
            & (Driver.organization_id == organization_id),
            isouter=True,
        )
        .where(
            DispatchDeliveryOrder.organization_id == organization_id,
            DispatchDeliveryOrder.status.notin_(['cancelled', 'failed']),
            DispatchDeliveryOrder.cash_settled_at.is_(None),
            DispatchDeliveryOrder.cod_amount_etb > 0,
        )
        .group_by(DispatchDeliveryOrder.driver_id, Driver.full_name)
    ).all()
    result = []
    for row in rows:
        expected = Decimal(row.expected or 0)
        collected = Decimal(row.collected or 0)
        shortfall = max(expected - collected, ZERO)
        factors = []
        score = 0
        if shortfall > 0:
            factors.append('cash shortfall')
        if int(row.outstanding_count or 0) >= 3:
            factors.append('multiple open stops')
        if expected >= Decimal('1000'):
            factors.append('high expected cash')
        if row.driver_id is None:
            factors.append('unassigned driver')
        score = min(
            100,
            (40 if shortfall > 0 else 0)
            + min(int(row.outstanding_count or 0) * 10, 30)
            + (20 if expected >= Decimal('1000') else 0)
            + (10 if row.driver_id is None else 0),
        )
        if score == 0:
            continue
        result.append(
            {
                'driver_id': str(row.driver_id) if row.driver_id else None,
                'driver_name': row.full_name or 'Unassigned driver',
                'outstanding_count': int(row.outstanding_count or 0),
                'expected_etb': expected,
                'collected_etb': collected,
                'shortfall_etb': shortfall,
                'risk_score': score,
                'factors': factors,
            }
        )
    return sorted(result, key=lambda row: int(row['risk_score']), reverse=True)[:10]


def build_decision_brief(db: Session, organization_id: UUID, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    triage = exception_triage(db, organization_id, now)
    cash_rows = cash_risk(db, organization_id)

    delayed_shipments = db.execute(
        select(func.count(Shipment.id)).where(
            Shipment.organization_id == organization_id,
            Shipment.status == 'delayed',
        )
    ).scalar_one()
    low_stock = db.execute(
        select(func.count(Inventory.id))
        .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
        .where(
            Warehouse.organization_id == organization_id,
            Inventory.quantity_on_hand < Inventory.safety_stock,
        )
    ).scalar_one()
    open_invoices = db.execute(
        select(func.count(RouteOptimizationRun.id)).where(
            RouteOptimizationRun.organization_id == organization_id,
            RouteOptimizationRun.unassigned_count > 0,
        )
    ).scalar_one()

    risks = []
    if delayed_shipments:
        risks.append(
            {
                'kind': 'delayed_shipments',
                'severity': 'high',
                'message': f'{delayed_shipments} shipment(s) are marked delayed.',
                'evidence': [
                    {
                        'record_type': 'shipment',
                        'label': 'delayed shipments',
                        'value': delayed_shipments,
                    }
                ],
            }
        )
    if low_stock:
        risks.append(
            {
                'kind': 'low_stock',
                'severity': 'high',
                'message': f'{low_stock} inventory row(s) are below safety stock.',
                'evidence': [{'record_type': 'inventory', 'label': 'below safety stock', 'value': low_stock}],
            }
        )
    if cash_rows:
        risks.append(
            {
                'kind': 'cash_exposure',
                'severity': 'high',
                'message': f'{len(cash_rows)} driver(s) have open cash exposure.',
                'evidence': [
                    {
                        'record_type': 'cash',
                        'label': 'expected outstanding',
                        'value': str(sum((row['shortfall_etb'] for row in cash_rows), ZERO)),
                    }
                ],
            }
        )
    if open_invoices:
        risks.append(
            {
                'kind': 'unassigned_route_history',
                'severity': 'medium',
                'message': f'{open_invoices} route run(s) contain unassigned deliveries.',
                'evidence': [
                    {
                        'record_type': 'route_history',
                        'label': 'runs with unassigned demand',
                        'value': open_invoices,
                    }
                ],
            }
        )
    if triage:
        risks.append(
            {
                'kind': 'exceptions',
                'severity': 'high' if triage[0]['priority'] >= 70 else 'medium',
                'message': f'{len(triage)} open exception(s) need an owner.',
                'evidence': [{'record_type': 'alert', 'label': 'open exceptions', 'value': len(triage)}],
            }
        )

    actions = []
    if triage:
        top = triage[0]
        actions.append(
            {
                'priority': 1,
                'action': top['suggested_action'],
                'reason': f"{top['title']} has been open for {top['age_hours']} hours.",
                'href': '/alerts',
                'evidence': top['evidence'],
            }
        )
    if cash_rows:
        top_cash = cash_rows[0]
        actions.append(
            {
                'priority': 2,
                'action': 'Reconcile the top cash exposure before closing the day.',
                'reason': f"{top_cash['driver_name']} has {top_cash['shortfall_etb']} ETB outstanding.",
                'href': '/dispatch',
                'evidence': [
                    {
                        'record_type': 'cash',
                        'label': 'shortfall',
                        'value': str(top_cash['shortfall_etb']),
                    }
                ],
            }
        )
    if low_stock:
        actions.append(
            {
                'priority': 3,
                'action': 'Review replenishment plans for the lowest-stock items.',
                'reason': 'Low stock can turn into a delivery failure if it is not handled before planning.',
                'href': '/planning',
                'evidence': [{'record_type': 'inventory', 'label': 'below safety stock', 'value': low_stock}],
            }
        )

    return {
        'generated_at': now,
        'generated_by': 'grounded_rules',
        'headline': (
            f'{len(risks)} operating risk(s) need review. '
            f'{len(actions)} recommended action(s) are available.'
        ),
        'what_changed': [
            f'{delayed_shipments} delayed shipment(s) are visible.',
            f'{len(triage)} open exception(s) are in the queue.',
            f'{len(cash_rows)} driver cash exposure group(s) are open.',
        ],
        'risks': risks,
        'actions': actions,
        'cash_risk': cash_rows,
        'triage': triage,
    }
