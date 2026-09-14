from __future__ import annotations

import asyncio
import json
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from app.api.security import actor_organization_id, get_current_user_from_token, scoped_to_organization
from app.core.observability import app_metrics
from app.db.session import get_db
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.route import RouteSchedule
from app.models.warehouse import Warehouse
from app.services.forecasting import forecast_weekly_demand
from app.services.live_feed import build_live_snapshot
from app.services.weather import simulated_weather_features

router = APIRouter()


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
        .join(Warehouse, Warehouse.id == HistoricalOrder.warehouse_id)
        .join(Item, Item.id == HistoricalOrder.item_id)
    )
    order_stmt = scoped_to_organization(order_stmt, HistoricalOrder, organization_id)
    rows = db.execute(order_stmt).all()

    forecast_rows = []
    if rows:
        orders: list[dict] = []
        weather_lookup: dict[str, dict[str, float]] = {}
        for row in rows:
            if row.weather_avg_temp_c is None or row.weather_precip_mm is None or row.weather_disruption_index is None:
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
            }
            for p in fc.predictions[:20]
        ]

    return build_live_snapshot(
        inventory_rows=inventory_rows,
        route_rows=route_rows,
        forecast_rows=forecast_rows,
    )


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
        user = get_current_user_from_token(token, db)
    except Exception:
        await websocket.close(code=1008, reason='Invalid or expired token')
        return

    # NB-64: resolve the subscriber's organization once, then stream only that
    # tenant's slice on every tick.
    organization_id = actor_organization_id(user, db)

    app_metrics.record_ws_open()

    try:
        while True:
            payload = _gather_snapshot(db, organization_id)
            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
