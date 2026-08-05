from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.api.security import require_roles, require_writable_workspace
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.route import RouteSchedule, RouteStop
from app.models.route_history import RouteOptimizationRun
from app.models.user import User
from app.models.warehouse import Warehouse
from app.repositories import RouteOptimizationRunRepository, RouteScheduleRepository, WarehouseRepository
from app.schemas.auth import UserRole
from app.schemas.route import (
    DeliveryDemand,
    RouteOptimizeRequest,
    RouteOptimizeResponse,
    RouteOptimizationRunDetail,
    RouteOptimizationRunSummary,
    RouteScheduleDetail,
    RouteScheduleSummary,
    RouteStopOut,
    RouteWeights,
)
from app.services.audit import record_audit_event, resolve_actor_organization_id
from app.services.metering import record_usage_for_user_membership
from app.services.routing import Delivery, Node, optimize_route_greedy

router = APIRouter()


@router.post('/optimize', response_model=RouteOptimizeResponse)
def optimize_routes(
    payload: RouteOptimizeRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    warehouses = db.execute(select(Warehouse)).scalars().all()
    if not warehouses:
        raise HTTPException(status_code=400, detail='No warehouses available')

    nodes = {w.code: Node(code=w.code, latitude=w.latitude, longitude=w.longitude) for w in warehouses}

    if payload.start_warehouse_code not in nodes:
        raise HTTPException(status_code=404, detail='start_warehouse_code not found')

    deliveries = [Delivery(warehouse_code=d.warehouse_code, demand_units=d.demand_units) for d in payload.deliveries]
    
    from app.utils.emissions import calculate_trip_emissions
    
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
    
    co2_saved_kg = None
    
    if payload.minimize_carbon_footprint:
        eco_result = optimize_route_greedy(
            nodes=nodes,
            start_code=payload.start_warehouse_code,
            deliveries=deliveries,
            vehicle_capacity_units=payload.vehicle_capacity_units,
            max_stops=payload.max_stops,
            speed_kmh=payload.speed_kmh,
            cost_per_km=payload.cost_per_km,
            weights={'distance': 1.0, 'time': 0.0, 'cost': 0.0},
        )
        
        co2_standard = calculate_trip_emissions(result['total_distance_km'] / 1.60934, 'heavy_duty')
        co2_eco = calculate_trip_emissions(eco_result['total_distance_km'] / 1.60934, 'heavy_duty')
        
        if co2_eco < co2_standard:
            result = eco_result
            co2_saved_kg = round(co2_standard - co2_eco, 2)
        else:
            co2_saved_kg = 0.0

    usage_recorded = record_usage_for_user_membership(
        db,
        user=actor,
        units=len(payload.deliveries),
    )

    serialized_stops = [RouteStopOut(**stop).model_dump(mode='json') for stop in result['stops']]
    organization_id = resolve_actor_organization_id(db, actor)

    history_run = RouteOptimizationRun(
        actor_user_id=actor.id,
        organization_id=organization_id,
        route_name=payload.route_name,
        schedule_date=payload.schedule_date,
        start_warehouse_code=payload.start_warehouse_code,
        vehicle_capacity_units=payload.vehicle_capacity_units,
        max_stops=payload.max_stops,
        speed_kmh=payload.speed_kmh,
        cost_per_km=payload.cost_per_km,
        objective=result['objective'],
        total_distance_km=result['total_distance_km'],
        total_cost=result['total_cost'],
        estimated_duration_min=result['estimated_duration_min'],
        capacity_used=result['capacity_used'],
        deliveries_count=len(payload.deliveries),
        stops_count=len(result['stops']),
        unassigned_count=len(result['unassigned_deliveries']),
        persist_requested=payload.persist_schedule,
        deliveries_json=[delivery.model_dump(mode='json') for delivery in payload.deliveries],
        weights_json=payload.weights.model_dump(mode='json'),
        stops_json=serialized_stops,
        unassigned_deliveries_json=[DeliveryDemand(**delivery).model_dump(mode='json') for delivery in result['unassigned_deliveries']],
        minimize_carbon_footprint=payload.minimize_carbon_footprint,
        co2_saved_kg=co2_saved_kg,
    )
    db.add(history_run)

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
        history_run.persisted_schedule_id = schedule.id

    record_audit_event(
        db,
        event_type='route.optimized',
        entity_type='route_optimization_run',
        entity_id=history_run.id,
        actor=actor,
        organization_id=organization_id,
        description=f'Optimized route scenario {payload.route_name}',
        payload={
            'deliveries_count': len(payload.deliveries),
            'persist_requested': payload.persist_schedule,
            'usage_recorded': usage_recorded,
            'unassigned_count': len(result['unassigned_deliveries']),
        },
    )

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
        co2_saved_kg=co2_saved_kg,
    )


@router.get('/schedules', response_model=list[RouteScheduleSummary])
def list_route_schedules(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    return RouteScheduleRepository(db).list_all_sorted()


@router.get('/schedules/{schedule_id}', response_model=RouteScheduleDetail)
def route_schedule_detail(
    schedule_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    schedule = RouteScheduleRepository(db).get_by_id(schedule_id)
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


@router.get('/history', response_model=list[RouteOptimizationRunSummary])
def list_route_optimization_history(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    return RouteOptimizationRunRepository(db).list_all_desc()


@router.get('/history/{run_id}', response_model=RouteOptimizationRunDetail)
def route_optimization_history_detail(
    run_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    run = RouteOptimizationRunRepository(db).get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail='Route optimization run not found')

    return RouteOptimizationRunDetail(
        id=run.id,
        created_at=run.created_at,
        route_name=run.route_name,
        schedule_date=run.schedule_date,
        start_warehouse_code=run.start_warehouse_code,
        objective=run.objective,
        total_distance_km=run.total_distance_km,
        total_cost=run.total_cost,
        estimated_duration_min=run.estimated_duration_min,
        capacity_used=run.capacity_used,
        deliveries_count=run.deliveries_count,
        stops_count=run.stops_count,
        unassigned_count=run.unassigned_count,
        persist_requested=run.persist_requested,
        persisted_schedule_id=run.persisted_schedule_id,
        actor_user_id=run.actor_user_id,
        organization_id=run.organization_id,
        vehicle_capacity_units=run.vehicle_capacity_units,
        max_stops=run.max_stops,
        speed_kmh=run.speed_kmh,
        cost_per_km=run.cost_per_km,
        weights=RouteWeights(**run.weights_json),
        deliveries=[DeliveryDemand(**delivery) for delivery in run.deliveries_json],
        stops=[RouteStopOut(**stop) for stop in run.stops_json],
        unassigned_deliveries=[DeliveryDemand(**delivery) for delivery in run.unassigned_deliveries_json],
        minimize_carbon_footprint=run.minimize_carbon_footprint,
        co2_saved_kg=run.co2_saved_kg,
    )
