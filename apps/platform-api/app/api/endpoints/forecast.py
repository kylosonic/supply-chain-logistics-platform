from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.order import HistoricalOrder
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.forecast import ForecastPoint, ForecastRequest, ForecastResponse
from app.services.forecasting import forecast_weekly_demand
from app.services.weather import simulated_weather_features

router = APIRouter()


@router.post('/weekly-demand', response_model=ForecastResponse)
def weekly_demand_forecast(
    payload: ForecastRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    # NB-64 (audit H-1): a forecast must be computed from the caller's own
    # order history, never from every tenant's combined demand.
    organization_id = resolve_scoped_organization(actor, writable) or actor_organization_id(actor, db)

    stmt = (
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
    stmt = scoped_to_organization(stmt, HistoricalOrder, organization_id)
    rows = db.execute(stmt).all()
    if not rows:
        raise HTTPException(status_code=400, detail='No historical orders found')

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

    output = forecast_weekly_demand(orders=orders, warehouse_weather_lookup=weather_lookup, horizon_weeks=payload.horizon_weeks)

    return ForecastResponse(
        horizon_weeks=payload.horizon_weeks,
        model_name=output.model_name,
        points=[ForecastPoint(**p) for p in output.predictions],
    )
