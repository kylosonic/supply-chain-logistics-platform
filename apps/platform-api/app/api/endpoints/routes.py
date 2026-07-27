from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.db.session import get_db
from app.models.route import RouteSchedule, RouteStop
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.route import RouteOptimizeRequest, RouteOptimizeResponse, RouteScheduleDetail, RouteScheduleSummary, RouteStopOut
from app.services.metering import record_usage_for_user_membership
from app.services.routing import Delivery, Node, optimize_route_greedy

router = APIRouter()


@router.post('/optimize', response_model=RouteOptimizeResponse)
def optimize_routes(
    payload: RouteOptimizeRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    warehouses = db.execute(select(Warehouse)).scalars().all()
    if not warehouses:
        raise HTTPException(status_code=400, detail='No warehouses available')

    nodes = {w.code: Node(code=w.code, latitude=w.latitude, longitude=w.longitude) for w in warehouses}

    if payload.start_warehouse_code not in nodes:
        raise HTTPException(status_code=404, detail='start_warehouse_code not found')

    deliveries = [Delivery(warehouse_code=d.warehouse_code, demand_units=d.demand_units) for d in payload.deliveries]
    result = optimize_route_greedy(
        nodes=nodes,
        start_code=payload.start_warehouse_code,
        deliveries=deliveries,
        vehicle_capacity_units=payload.vehicle_capacity_units,
        max_stops=payload.max_stops,
        speed_kmh=payload.speed_kmh,
        cost_per_km=payload.cost_per_km,
        weights=payload.weights.model_dump(),
    )

    usage_recorded = record_usage_for_user_membership(
        db,
        user=actor,
        units=len(payload.deliveries),
    )

    if payload.persist_schedule:
        start_wh = db.execute(select(Warehouse).where(Warehouse.code == payload.start_warehouse_code)).scalar_one()
        schedule = RouteSchedule(
            route_name=payload.route_name,
            schedule_date=payload.schedule_date,
            start_warehouse_id=start_wh.id,
            vehicle_capacity_units=payload.vehicle_capacity_units,
            objective=result['objective'],
            total_distance_km=result['total_distance_km'],
            total_cost=result['total_cost'],
            estimated_duration_min=result['estimated_duration_min'],
            status='planned',
        )
        db.add(schedule)
        db.flush()

        current_time = datetime.now(UTC)
        for stop in result['stops']:
            row_wh = db.execute(select(Warehouse).where(Warehouse.code == stop['warehouse_code'])).scalar_one_or_none()
            if not row_wh:
                continue
            arrival = stop['estimated_arrival']
            departure = arrival + timedelta(minutes=10)
            rs = RouteStop(
                route_schedule_id=schedule.id,
                sequence=stop['sequence'],
                warehouse_id=row_wh.id,
                planned_arrival=arrival,
                planned_departure=departure,
                load_units=stop['demand_units'],
                notes=f"generated_at={current_time.isoformat()}",
            )
            db.add(rs)

        db.commit()
    elif usage_recorded:
        db.commit()

    return RouteOptimizeResponse(
        route_name=payload.route_name,
        schedule_date=payload.schedule_date,
        objective=result['objective'],
        total_distance_km=result['total_distance_km'],
        total_cost=result['total_cost'],
        estimated_duration_min=result['estimated_duration_min'],
        capacity_used=result['capacity_used'],
        unassigned_deliveries=result['unassigned_deliveries'],
        stops=[RouteStopOut(**s) for s in result['stops']],
    )


@router.get('/schedules', response_model=list[RouteScheduleSummary])
def list_route_schedules(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    rows = db.execute(select(RouteSchedule).order_by(asc(RouteSchedule.schedule_date), asc(RouteSchedule.route_name))).scalars().all()
    return rows


@router.get('/schedules/{schedule_id}', response_model=RouteScheduleDetail)
def route_schedule_detail(
    schedule_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    schedule = db.get(RouteSchedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail='Route schedule not found')

    stops = db.execute(
        select(RouteStop, Warehouse.code, Warehouse.latitude, Warehouse.longitude)
        .join(Warehouse, Warehouse.id == RouteStop.warehouse_id)
        .where(RouteStop.route_schedule_id == schedule_id)
        .order_by(asc(RouteStop.sequence))
    ).all()

    stop_payload = [
        RouteStopOut(
            sequence=s.RouteStop.sequence,
            warehouse_code=s.code,
            demand_units=s.RouteStop.load_units,
            leg_distance_km=0.0,
            cumulative_distance_km=0.0,
            latitude=s.latitude,
            longitude=s.longitude,
            estimated_arrival=s.RouteStop.planned_arrival,
        )
        for s in stops
    ]

    return RouteScheduleDetail(
        id=schedule.id,
        route_name=schedule.route_name,
        schedule_date=schedule.schedule_date,
        total_distance_km=schedule.total_distance_km,
        total_cost=schedule.total_cost,
        estimated_duration_min=schedule.estimated_duration_min,
        status=schedule.status,
        stops=stop_payload,
    )
