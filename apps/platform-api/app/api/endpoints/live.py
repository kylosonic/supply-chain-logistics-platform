from __future__ import annotations

import asyncio
import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from app.api.security import get_current_user_from_token, scoped_to_organization
from app.core.observability import app_metrics
from app.db.session import get_db
from app.models.dispatch import DeliveryOrder, DispatchRun
from app.models.driver import Driver
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.organization import Organization
from app.models.route import RouteSchedule
from app.models.warehouse import Warehouse
from app.repositories import MembershipRepository
from app.services.forecasting import forecast_weekly_demand
from app.services.live_feed import build_live_snapshot
from app.services.security import decode_access_token
from app.services.weather import simulated_weather_features

router = APIRouter()

_TERMINAL_DISPATCH_STATUSES = frozenset({'delivered', 'failed', 'cancelled'})


def _live_principal(token: str, db: Session):
    payload = decode_access_token(token)
    organization_claim = payload.get('org_id')
    if not organization_claim:
        raise ValueError('Organization-scoped token required')
    user = get_current_user_from_token(token, db)
    membership = MembershipRepository(db).get_active_membership(
        user.id,
        org_id=organization_claim,
    )
    if membership is None:
        raise ValueError('No active organization membership')
    organization = db.get(Organization, membership.organization_id)
    if organization is None or not organization.is_active:
        raise ValueError('Workspace is inactive')
    return user, membership, organization


def _gather_snapshot(db: Session, organization_id: UUID | None = None) -> dict:
    # NB-64 (audit H-1): the live snapshot is tenant data. An org-scoped
    # subscriber receives only their own warehouses/items/routes/orders.
    inventory_stmt = (
        select(
            Warehouse.code.label('warehouse_code'),
            Warehouse.name.label('warehouse_name'),
            func.coalesce(func.sum(Inventory.quantity_on_hand), 0).label('total_quantity_on_hand'),
            func.coalesce(func.sum(Inventory.safety_stock), 0).label('total_safety_stock'),
            func.max(Warehouse.capacity_units).label('capacity_units'),
        )
        .join(Inventory, Inventory.warehouse_id == Warehouse.id, isouter=True)
        .group_by(Warehouse.code, Warehouse.name)
        .order_by(Warehouse.code)
    )
    inventory_stmt = scoped_to_organization(inventory_stmt, Warehouse, organization_id)
    inventory_rows = []
    for row in db.execute(inventory_stmt).all():
        utilization = (row.total_quantity_on_hand / row.capacity_units * 100.0) if row.capacity_units else 0.0
        inventory_rows.append(
            {
                'warehouse_code': row.warehouse_code,
                'warehouse_name': row.warehouse_name,
                'total_quantity_on_hand': int(row.total_quantity_on_hand),
                'total_safety_stock': int(row.total_safety_stock),
                'utilization_percent': round(utilization, 2),
            }
        )

    route_stmt = scoped_to_organization(select(RouteSchedule), RouteSchedule, organization_id)
    route_rows = [
        {
            'id': r.id,
            'route_name': r.route_name,
            'schedule_date': str(r.schedule_date),
            'total_distance_km': r.total_distance_km,
            'total_cost': r.total_cost,
            'estimated_duration_min': r.estimated_duration_min,
            'status': r.status,
        }
        for r in db.execute(
            route_stmt
            .order_by(asc(RouteSchedule.schedule_date), asc(RouteSchedule.route_name))
            .limit(10)
        ).scalars().all()
    ]

    order_stmt = (
        select(
            HistoricalOrder.order_date,
            HistoricalOrder.quantity,
            HistoricalOrder.weather_avg_temp_c,
            HistoricalOrder.weather_precip_mm,
            HistoricalOrder.weather_disruption_index,
            Warehouse.code.label('warehouse_code'),
            Warehouse.latitude,
            Warehouse.longitude,
            Item.sku.label('sku'),
        )
        .join(
            Warehouse,
            (Warehouse.id == HistoricalOrder.warehouse_id)
            & (Warehouse.organization_id == organization_id),
        )
        .join(
            Item,
            (Item.id == HistoricalOrder.item_id)
            & (Item.organization_id == organization_id),
        )
    )
    order_stmt = scoped_to_organization(order_stmt, HistoricalOrder, organization_id)
    rows = db.execute(order_stmt).all()

    forecast_rows = []
    if rows:
        orders: list[dict] = []
        weather_lookup: dict[str, dict[str, float]] = {}
        for row in rows:
            if (
                row.weather_avg_temp_c is None
                or row.weather_precip_mm is None
                or row.weather_disruption_index is None
            ):
                w = simulated_weather_features(date.today(), row.latitude, row.longitude)
                temp = w['weather_avg_temp_c']
                precip = w['weather_precip_mm']
                disruption = w['weather_disruption_index']
            else:
                temp = row.weather_avg_temp_c
                precip = row.weather_precip_mm
                disruption = row.weather_disruption_index

            orders.append(
                {
                    'order_date': row.order_date,
                    'quantity': row.quantity,
                    'warehouse_code': row.warehouse_code,
                    'sku': row.sku,
                    'weather_avg_temp_c': temp,
                    'weather_precip_mm': precip,
                    'weather_disruption_index': disruption,
                }
            )
            weather_lookup[row.warehouse_code] = {
                'weather_avg_temp_c': temp,
                'weather_precip_mm': precip,
                'weather_disruption_index': disruption,
            }

        fc = forecast_weekly_demand(orders=orders, warehouse_weather_lookup=weather_lookup, horizon_weeks=1)
        forecast_rows = [
            {
                'week_start': str(p['week_start']),
                'warehouse_code': p['warehouse_code'],
                'sku': p['sku'],
                'predicted_demand': p['predicted_demand'],
                'planning_low': p['planning_low'],
                'planning_high': p['planning_high'],
            }
            for p in fc.predictions[:20]
        ]

    dispatch_overview = _dispatch_overview(db, organization_id)
    return build_live_snapshot(
        inventory_rows=inventory_rows,
        route_rows=route_rows,
        forecast_rows=forecast_rows,
        dispatch_overview=dispatch_overview,
    )


def _dispatch_overview(db: Session, organization_id: UUID | None) -> dict:
    """Return a small, tenant-scoped execution view for live subscribers.

    The console uses ``updated_at`` as a version marker. It only needs to
    refetch its fuller dispatch runs when the underlying orders or runs change,
    rather than on every five-second socket tick.
    """
    if organization_id is None:
        return {'updated_at': None, 'runs': []}

    run_rows = db.execute(
        select(DispatchRun, Driver.full_name)
        .outerjoin(
            Driver,
            (Driver.id == DispatchRun.driver_id)
            & (Driver.organization_id == organization_id),
        )
        .where(DispatchRun.organization_id == organization_id)
        .order_by(DispatchRun.updated_at.desc(), DispatchRun.id)
        .limit(25)
    ).all()
    if not run_rows:
        return {'updated_at': None, 'runs': []}

    run_ids = [run.id for run, _driver_name in run_rows]
    orders = (
        db.execute(
            select(DeliveryOrder).where(
                DeliveryOrder.organization_id == organization_id,
                DeliveryOrder.dispatch_run_id.in_(run_ids),
            )
        )
        .scalars()
        .all()
    )

    orders_by_run: dict[UUID, list[DeliveryOrder]] = {}
    for order in orders:
        if order.dispatch_run_id is not None:
            orders_by_run.setdefault(order.dispatch_run_id, []).append(order)

    latest_update: datetime | None = None
    summaries: list[dict] = []
    for run, driver_name in run_rows:
        run_orders = orders_by_run.get(run.id, [])
        terminal_count = sum(
            order.status in _TERMINAL_DISPATCH_STATUSES for order in run_orders
        )
        collected_cash = sum(
            (order.collected_cash_etb or Decimal('0.00') for order in run_orders),
            Decimal('0.00'),
        )
        run_latest = max(
            (order.updated_at for order in run_orders if order.updated_at is not None),
            default=run.updated_at,
        )
        if run_latest is not None and (
            latest_update is None or run_latest > latest_update
        ):
            latest_update = run_latest

        summaries.append(
            {
                'id': str(run.id),
                'route_name': run.route_name,
                'plan_date': run.plan_date.isoformat(),
                'status': run.status,
                'driver_id': str(run.driver_id) if run.driver_id else None,
                'driver_name': driver_name,
                'total_stops': len(run_orders),
                'terminal_stops': terminal_count,
                'progress_percent': (
                    round((terminal_count / len(run_orders)) * 100, 2)
                    if run_orders
                    else 0.0
                ),
                'expected_cash_etb': str(run.expected_cash_etb),
                'collected_cash_etb': str(collected_cash),
                'cash_declared_etb': (
                    str(run.cash_declared_etb)
                    if run.cash_declared_etb is not None
                    else None
                ),
                'cash_handed_over_etb': (
                    str(run.cash_handed_over_etb)
                    if run.cash_handed_over_etb is not None
                    else None
                ),
                'cash_shortfall_etb': (
                    str(run.cash_shortfall_etb)
                    if run.cash_shortfall_etb is not None
                    else None
                ),
                'cash_overage_etb': (
                    str(run.cash_overage_etb)
                    if run.cash_overage_etb is not None
                    else None
                ),
                'cash_deposit_bank': run.cash_deposit_bank,
                'cash_deposit_reference': run.cash_deposit_reference,
                'cash_closed_at': (
                    run.cash_closed_at.isoformat() if run.cash_closed_at else None
                ),
                'updated_at': run_latest.isoformat() if run_latest else None,
            }
        )

    return {
        'updated_at': latest_update.isoformat() if latest_update is not None else None,
        'runs': summaries,
    }


@router.websocket('/updates')
async def websocket_updates(
    websocket: WebSocket,
    db: Session = Depends(get_db),
):
    await websocket.accept()
    auth_msg = await websocket.receive_text()
    try:
        parsed = json.loads(auth_msg)
    except json.JSONDecodeError:
        await websocket.close(code=1008, reason='Invalid auth payload')
        return

    token = parsed.get('token')
    if not token:
        await websocket.close(code=1008, reason='Missing token')
        return

    try:
        _user, membership, _organization = _live_principal(token, db)
    except Exception:
        await websocket.close(code=1008, reason='Invalid, expired, or unauthorized token')
        return
    organization_id = membership.organization_id

    app_metrics.record_ws_open()

    try:
        while True:
            # A socket is not a permanent capability. Revalidate the user,
            # membership, organization, and token expiry before every snapshot
            # so a revoked member cannot keep receiving tenant data.
            db.expire_all()
            try:
                _live_principal(token, db)
            except Exception:
                await websocket.close(code=1008, reason='Session is no longer authorized')
                return
            payload = _gather_snapshot(db, organization_id)
            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
