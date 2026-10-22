from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.route_history import RouteOptimizationRun
from app.models.warehouse import Warehouse


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def _run(route_name: str, organization_id: UUID | None) -> RouteOptimizationRun:
    return RouteOptimizationRun(
        actor_user_id=None,
        organization_id=organization_id,
        persisted_schedule_id=None,
        route_name=route_name,
        schedule_date=date(2026, 8, 10),
        start_warehouse_code='WH-001',
        vehicle_capacity_units=100,
        max_stops=5,
        speed_kmh=45,
        cost_per_km=1.5,
        objective='weighted_cost',
        total_distance_km=10,
        total_cost=15,
        estimated_duration_min=20,
        capacity_used=10,
        deliveries_count=1,
        stops_count=1,
        unassigned_count=0,
        persist_requested=False,
        deliveries_json=[{'warehouse_code': 'WH-002', 'demand_units': 10}],
        weights_json={'distance': 0.5, 'time': 0.3, 'cost': 0.2},
        stops_json=[],
        unassigned_deliveries_json=[],
        minimize_carbon_footprint=False,
        co2_saved_kg=None,
        explanation_json=None,
    )


def test_route_history_null_org_rows_are_not_globally_visible(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    org_a, token_a = signup_workspace('Route Scope A')
    org_b, token_b = signup_workspace('Route Scope B')
    own_a = _run('A-Only Route', UUID(org_a))
    own_b = _run('B-Only Route', UUID(org_b))
    legacy = _run('Legacy Null Route', None)
    db_session.add_all([own_a, own_b, legacy])
    db_session.commit()

    history_a = client.get('/api/v1/routes/history', headers=_headers(token_a))
    assert history_a.status_code == 200, history_a.text
    assert {item['route_name'] for item in history_a.json()} == {'A-Only Route'}

    history_b = client.get('/api/v1/routes/history', headers=_headers(token_b))
    assert history_b.status_code == 200, history_b.text
    assert {item['route_name'] for item in history_b.json()} == {'B-Only Route'}

    null_from_a = client.get(
        f'/api/v1/routes/history/{legacy.id}',
        headers=_headers(token_a),
    )
    assert null_from_a.status_code == 404
    foreign_from_a = client.get(
        f'/api/v1/routes/history/{own_b.id}',
        headers=_headers(token_a),
    )
    assert foreign_from_a.status_code == 404


def test_orgless_actor_cannot_read_route_history(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
    orgless_token: str,
):
    org_a, _token_a = signup_workspace('Route Scope Tenant')
    tenant_run = _run('Tenant Route', UUID(org_a))
    legacy_run = _run('Legacy Own Route', None)
    db_session.add_all([tenant_run, legacy_run])
    db_session.commit()

    history = client.get('/api/v1/routes/history', headers=_headers(orgless_token))
    assert history.status_code == 403, history.text

    tenant_detail = client.get(
        f'/api/v1/routes/history/{tenant_run.id}',
        headers=_headers(orgless_token),
    )
    assert tenant_detail.status_code == 403

    legacy_detail = client.get(
        f'/api/v1/routes/history/{legacy_run.id}',
        headers=_headers(orgless_token),
    )
    assert legacy_detail.status_code == 403


def test_orgless_optimization_is_denied_before_warehouse_access(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
    orgless_token: str,
):
    _org_a, _token_a = signup_workspace('Warehouse Boundary Ltd')

    response = client.post(
        '/api/v1/routes/optimize',
        headers=_headers(orgless_token),
        json={
            'route_name': 'Must Not Use Tenant Warehouses',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
            'vehicle_capacity_units': 100,
            'max_stops': 5,
            'persist_schedule': False,
        },
    )

    assert response.status_code == 403, response.text
    assert response.json()['detail'] == 'No active organization membership'
    assert db_session.query(RouteOptimizationRun).count() == 0


def test_tenant_optimization_cannot_target_null_org_warehouses(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _org_a, token_a = signup_workspace('Tenant Warehouse Boundary Ltd')
    db_session.add(
        Warehouse(
            code='WH-GLOBAL',
            name='Legacy Global Warehouse',
            address='Address',
            city='City',
            state='State',
            country='ET',
            latitude=9.02,
            longitude=38.73,
            capacity_units=1000,
        )
    )
    db_session.commit()

    response = client.post(
        '/api/v1/routes/optimize',
        headers=_headers(token_a),
        json={
            'route_name': 'Must Not Read Legacy Rows',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-GLOBAL', 'demand_units': 10}],
            'vehicle_capacity_units': 100,
            'max_stops': 5,
            'persist_schedule': False,
        },
    )

    assert response.status_code == 422, response.text
    assert db_session.query(RouteOptimizationRun).count() == 0
