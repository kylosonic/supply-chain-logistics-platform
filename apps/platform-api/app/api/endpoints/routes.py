from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, or_, select
from sqlalchemy.orm import Session

from app.api.security import (
    actor_organization_id,
    order_by_organization_first,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    scoped_to_organization,
)
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.route import RouteSchedule, RouteStop
from app.models.route_history import RouteOptimizationRun
from app.models.user import User
from app.models.warehouse import Warehouse
from app.repositories import RouteOptimizationRunRepository, RouteScheduleRepository
from app.schemas.auth import UserRole
from app.schemas.route import (
    DeliveryDemand,
    RouteOptimizationRunDetail,
    RouteOptimizationRunSummary,
    RouteOptimizeRequest,
    RouteOptimizeResponse,
    RouteScheduleDetail,
    RouteScheduleSummary,
    RouteStopOut,
    RouteWeights,
)
from app.services.activation.state import record_route_optimization
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
    # TECH-57: org resolution FIRST — every warehouse query below must be
    # org-scoped so identical seeded codes across orgs (WH-001..003) can
    # never collide (MultipleResultsFound -> 500 on persist=true).
    organization_id = resolve_actor_organization_id(db, actor)

    nodes_query = scoped_to_organization(select(Warehouse), Warehouse, organization_id)
    warehouses = db.execute(nodes_query).scalars().all()
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
    # NB-31.1 gap-fill: the route_optimizations meter was never recorded;
    # both Free-cap meters must be able to hit the cap (decision #12).
    usage_recorded_optimizations = record_usage_for_user_membership(
        db,
        user=actor,
        metric='route_optimizations',
        units=1,
    )

    serialized_stops = [RouteStopOut(**stop).model_dump(mode='json') for stop in result['stops']]

    # NB-27.3: audit the data substrate of the run (decision #4) — real iff
    # the start warehouse AND every delivery-target warehouse row used in
    # the run exist with data_origin='real' (one IN-select, not N queries).
    used_codes = {payload.start_warehouse_code} | {d.warehouse_code for d in payload.deliveries}
    origin_query = scoped_to_organization(
        select(Warehouse.code, Warehouse.data_origin).where(Warehouse.code.in_(list(used_codes))),
        Warehouse,
        organization_id,
    )
    origin_rows = db.execute(origin_query).all()
    origin_by_code = {row.code: row.data_origin for row in origin_rows}
    run_origin = 'real'
    for code in used_codes:
        if origin_by_code.get(code) != 'real':
            run_origin = 'sample'
            break

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
        start_query = order_by_organization_first(
            scoped_to_organization(
                select(Warehouse).where(Warehouse.code == payload.start_warehouse_code),
                Warehouse,
                organization_id,
            ),
            Warehouse,
        )
        start_wh = db.execute(start_query).scalars().first()
        if start_wh is None:
            raise HTTPException(status_code=404, detail='start_warehouse_code not found')
        schedule = RouteSchedule(
            organization_id=organization_id or start_wh.organization_id,
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
            stop_query = order_by_organization_first(
                scoped_to_organization(
                    select(Warehouse).where(Warehouse.code == stop['warehouse_code']),
                    Warehouse,
                    organization_id,
                ),
                Warehouse,
            )
            row_wh = db.execute(stop_query).scalars().first()
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
            'data_origin': run_origin,
            'usage_recorded_optimizations': usage_recorded_optimizations,
        },
    )

    # NB-28.4/33: milestone 6 = first route optimization, ANY substrate.
    # post_aha_toast surfaces exactly on that first transition (server truth).
    # Org-less runs (admin with no membership) skip activation — the state
    # row is 1:1 with an organization and cannot be keyed by NULL.
    db.flush()
    post_aha_toast = False
    if organization_id is not None:
        post_aha_toast = record_route_optimization(
            db,
            organization_id,
            history_run.id,
            data_origin=run_origin,
            now=datetime.now(UTC),
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
        post_aha_toast=post_aha_toast,
        data_origin=run_origin,
    )


@router.get('/schedules', response_model=list[RouteScheduleSummary])
def list_route_schedules(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64 (audit H-1): route schedules are tenant data.
    return RouteScheduleRepository(db).list_all_sorted(actor_organization_id(actor, db))


@router.get('/schedules/{schedule_id}', response_model=RouteScheduleDetail)
def route_schedule_detail(
    schedule_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    schedule = organization_scoped_get(
        db,
        RouteSchedule,
        schedule_id,
        actor_organization_id(actor, db),
        not_found_detail='Route schedule not found',
    )

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
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    # NB-64: run history carries route names, warehouse codes and costs.
    return RouteOptimizationRunRepository(db).list_all_desc(actor_organization_id(actor, db))


@router.get('/history/{run_id}', response_model=RouteOptimizationRunDetail)
def route_optimization_history_detail(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    run = organization_scoped_get(
        db,
        RouteOptimizationRun,
        run_id,
        actor_organization_id(actor, db),
        not_found_detail='Route optimization run not found',
    )

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
