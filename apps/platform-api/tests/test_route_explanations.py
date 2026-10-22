from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.endpoints import routes as routes_endpoint
from app.models.route_history import RouteOptimizationRun
from app.services.route_explanations import build_route_explanation
from app.services.routing import Delivery, Node, optimize_route_greedy

NODES = {
    'WH-001': Node(code='WH-001', latitude=9.03, longitude=38.74),
    'WH-002': Node(code='WH-002', latitude=9.04, longitude=38.75),
    'WH-003': Node(code='WH-003', latitude=9.10, longitude=38.82),
    'WH-004': Node(code='WH-004', latitude=9.05, longitude=38.76),
    'WH-005': Node(code='WH-005', latitude=9.055, longitude=38.765),
    'WH-006': Node(code='WH-006', latitude=9.06, longitude=38.77),
}

DELIVERIES = [
    Delivery(warehouse_code='WH-002', demand_units=10),
    Delivery(warehouse_code='WH-003', demand_units=10),
]


def _optimize(weights: dict[str, float], forced_first_code: str | None = None) -> dict:
    return optimize_route_greedy(
        nodes=NODES,
        start_code='WH-001',
        deliveries=DELIVERIES,
        vehicle_capacity_units=100,
        max_stops=5,
        speed_kmh=45,
        cost_per_km=1.5,
        weights=weights,
        forced_first_code=forced_first_code,
    )


def test_explanation_uses_real_runner_up_and_configured_factor():
    weights = {'distance': 0.5, 'time': 0.3, 'cost': 0.2}
    selected = _optimize(weights)
    runner_up_code = selected['decision_trace'][0]['runner_up_warehouse_code']
    alternative = _optimize(weights, forced_first_code=runner_up_code)

    explanation = build_route_explanation(
        selected,
        alternative,
        vehicle_capacity_units=100,
        max_stops=5,
    )

    assert explanation['method'] == 'deterministic_weighted_greedy'
    assert explanation['dominant_factor'] in {'distance', 'time', 'cost'}
    assert explanation['factor_share_pct'][explanation['dominant_factor']] > 0
    assert len(explanation['decision_points']) == 2
    assert explanation['decision_points'][0]['runner_up_warehouse_code'] is not None
    assert explanation['runner_up'] is not None
    assert explanation['runner_up']['first_stop_warehouse_code'] == runner_up_code
    assert 'largest share' in explanation['summary']
    assert any('proportional to leg distance' in item for item in explanation['limitations'])


def test_zero_weights_do_not_fabricate_a_dominant_factor():
    selected = _optimize({'distance': 0.0, 'time': 0.0, 'cost': 0.0})
    explanation = build_route_explanation(
        selected,
        None,
        vehicle_capacity_units=100,
        max_stops=5,
    )

    assert selected['decision_trace'][0]['dominant_factor'] == 'none'
    assert explanation['dominant_factor'] == 'none'
    assert 'no factor could dominate' in explanation['summary']
    assert explanation['runner_up'] is None


def test_eco_selected_route_persists_the_effective_weights(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
    monkeypatch,
):
    _organization_id, token = signup_workspace('Eco Weights Ltd')
    real_optimize = routes_endpoint.optimize_route_greedy

    def distance_biased_optimize(**kwargs):
        result = dict(real_optimize(**kwargs))
        selected_weights = kwargs['weights']
        is_eco = selected_weights.get('distance') == 1.0 and selected_weights.get('time') == 0.0
        result['total_distance_km'] = 1.0 if is_eco else 100.0
        return result

    monkeypatch.setattr(routes_endpoint, 'optimize_route_greedy', distance_biased_optimize)
    response = client.post(
        '/api/v1/routes/optimize',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'route_name': 'Eco Route',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
            'vehicle_capacity_units': 200,
            'max_stops': 5,
            'persist_schedule': False,
            'minimize_carbon_footprint': True,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()['co2_saved_kg'] > 0
    run = db_session.execute(select(RouteOptimizationRun)).scalars().one()
    assert run.weights_json == {'distance': 1.0, 'time': 0.0, 'cost': 0.0}


def test_remaining_capacity_is_reported_when_no_unassigned_delivery_fits():
    selected = optimize_route_greedy(
        nodes=NODES,
        start_code='WH-001',
        deliveries=DELIVERIES,
        vehicle_capacity_units=15,
        max_stops=5,
        speed_kmh=45,
        cost_per_km=1.5,
        weights={'distance': 0.5, 'time': 0.3, 'cost': 0.2},
    )

    explanation = build_route_explanation(
        selected,
        None,
        vehicle_capacity_units=15,
        max_stops=5,
    )

    assert selected['capacity_used'] == 10
    assert len(selected['unassigned_deliveries']) == 1
    assert any(
        'Remaining vehicle capacity (5 of 15 units) is too small for 1 unassigned delivery.'
        in constraint
        for constraint in explanation['constraints']
    )
    assert not any('max_stops limit' in constraint for constraint in explanation['constraints'])


def test_capacity_exclusions_count_distinct_targets_not_repeated_decisions():
    selected = optimize_route_greedy(
        nodes=NODES,
        start_code='WH-001',
        deliveries=[
            Delivery(warehouse_code='WH-002', demand_units=10),
            Delivery(warehouse_code='WH-003', demand_units=10),
            Delivery(warehouse_code='WH-006', demand_units=150),
        ],
        vehicle_capacity_units=100,
        max_stops=5,
        speed_kmh=45,
        cost_per_km=1.5,
        weights={'distance': 0.5, 'time': 0.3, 'cost': 0.2},
    )

    explanation = build_route_explanation(
        selected,
        None,
        vehicle_capacity_units=100,
        max_stops=5,
    )

    assert sum(
        point['capacity_excluded_count'] for point in selected['decision_trace']
    ) > selected['capacity_excluded_count']
    assert selected['capacity_excluded_count'] == 1
    assert any(
        'excluded 1 distinct delivery target' in constraint
        for constraint in explanation['constraints']
    )
    assert not any(
        'excluded 2 distinct delivery targets' in constraint
        for constraint in explanation['constraints']
    )


def test_max_stop_constraint_is_reported_when_capacity_is_not_the_blocker():
    selected = optimize_route_greedy(
        nodes=NODES,
        start_code='WH-001',
        deliveries=[
            Delivery(warehouse_code='WH-002', demand_units=5),
            Delivery(warehouse_code='WH-003', demand_units=5),
            Delivery(warehouse_code='WH-004', demand_units=5),
        ],
        vehicle_capacity_units=100,
        max_stops=1,
        speed_kmh=45,
        cost_per_km=1.5,
        weights={'distance': 0.5, 'time': 0.3, 'cost': 0.2},
    )

    explanation = build_route_explanation(
        selected,
        None,
        vehicle_capacity_units=100,
        max_stops=1,
    )

    assert len(selected['stops']) == 1
    assert len(selected['unassigned_deliveries']) == 2
    assert any('max_stops limit of 1 was reached' in item for item in explanation['constraints'])


def test_duplicate_and_unknown_delivery_targets_are_rejected_at_the_api_boundary(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _organization_id, token = signup_workspace('Delivery Integrity Ltd')
    headers = {'Authorization': f'Bearer {token}'}

    duplicate = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={
            'route_name': 'Duplicate Demand',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [
                {'warehouse_code': 'WH-002', 'demand_units': 10},
                {'warehouse_code': 'WH-002', 'demand_units': 10},
            ],
            'vehicle_capacity_units': 15,
            'max_stops': 5,
            'persist_schedule': False,
        },
    )
    assert duplicate.status_code == 200, duplicate.text
    duplicate_body = duplicate.json()
    assert duplicate_body['stops'] == []
    assert sum(
        item['demand_units'] for item in duplicate_body['unassigned_deliveries']
    ) == 20
    assert len(duplicate_body['unassigned_deliveries']) == 2
    assert any(
        '1 distinct delivery target' in constraint
        for constraint in duplicate_body['decision_explanation']['constraints']
    )

    for target in ('WH-UNKNOWN', 'WH-001'):
        rejected = client.post(
            '/api/v1/routes/optimize',
            headers=headers,
            json={
                'route_name': 'Invalid Target',
                'schedule_date': '2026-08-10',
                'start_warehouse_code': 'WH-001',
                'deliveries': [{'warehouse_code': target, 'demand_units': 10}],
                'vehicle_capacity_units': 100,
                'max_stops': 5,
                'persist_schedule': False,
            },
        )
        assert rejected.status_code == 422, rejected.text

    assert db_session.execute(select(RouteOptimizationRun)).scalars().all()[0].route_name == (
        'Duplicate Demand'
    )
    assert len(db_session.execute(select(RouteOptimizationRun)).scalars().all()) == 1


def test_route_payload_size_limits_are_enforced(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _organization_id, token = signup_workspace('Bounded Routes Ltd')
    headers = {'Authorization': f'Bearer {token}'}
    base = {
        'route_name': 'Bounded Route',
        'schedule_date': '2026-08-10',
        'start_warehouse_code': 'WH-001',
        'vehicle_capacity_units': 100,
        'max_stops': 5,
        'persist_schedule': False,
    }

    too_many_deliveries = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={
            **base,
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 1}] * 201,
        },
    )
    assert too_many_deliveries.status_code == 422

    too_many_stops = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={
            **base,
            'max_stops': 101,
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 1}],
        },
    )
    assert too_many_stops.status_code == 422

    empty_deliveries = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={**base, 'deliveries': []},
    )
    assert empty_deliveries.status_code == 422
    assert db_session.execute(select(RouteOptimizationRun)).scalars().all() == []


def test_optimize_response_and_history_detail_include_the_explanation(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _organization_id, token = signup_workspace('Explainable Routes Ltd')
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={
            'route_name': 'Explainable Route',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [
                {'warehouse_code': 'WH-002', 'demand_units': 10},
                {'warehouse_code': 'WH-003', 'demand_units': 5},
            ],
            'vehicle_capacity_units': 200,
            'max_stops': 5,
            'speed_kmh': 45,
            'cost_per_km': 1.5,
            'persist_schedule': True,
            'minimize_carbon_footprint': False,
        },
    )

    assert response.status_code == 200, response.text
    explanation = response.json()['decision_explanation']
    assert explanation is not None
    assert explanation['summary']
    assert explanation['decision_points']
    assert explanation['runner_up'] is not None

    run = db_session.execute(select(RouteOptimizationRun)).scalars().one()
    assert run.explanation_json is not None
    assert run.explanation_json['summary'] == explanation['summary']

    detail = client.get(f'/api/v1/routes/history/{run.id}', headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()['decision_explanation'] == explanation


def test_history_detail_keeps_runs_without_explanations_compatible(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _organization_id, token = signup_workspace('Legacy Routes Ltd')
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={
            'route_name': 'Legacy Route',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
            'vehicle_capacity_units': 200,
            'max_stops': 5,
            'persist_schedule': False,
        },
    )
    assert response.status_code == 200, response.text

    run = db_session.execute(select(RouteOptimizationRun)).scalars().one()
    run.explanation_json = None
    db_session.commit()

    detail = client.get(f'/api/v1/routes/history/{run.id}', headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()['decision_explanation'] is None


def test_history_detail_explanation_is_tenant_scoped(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _, token_a = signup_workspace('Explanation Iso A')
    _, token_b = signup_workspace('Explanation Iso B')
    response = client.post(
        '/api/v1/routes/optimize',
        headers={'Authorization': f'Bearer {token_b}'},
        json={
            'route_name': 'Private Decision',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
            'vehicle_capacity_units': 200,
            'max_stops': 5,
            'persist_schedule': False,
        },
    )
    assert response.status_code == 200, response.text
    run = db_session.execute(select(RouteOptimizationRun)).scalars().one()

    detail = client.get(
        f'/api/v1/routes/history/{run.id}',
        headers={'Authorization': f'Bearer {token_a}'},
    )
    assert detail.status_code == 404, detail.text
    assert detail.json()['detail'] == 'Route optimization run not found'


def test_history_detail_returns_a_controlled_error_for_malformed_ids_and_json(
    client: TestClient,
    db_session: Session,
    signup_workspace,
    seed_csv_path,
):
    _organization_id, token = signup_workspace('Corrupt Explanation Ltd')
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post(
        '/api/v1/routes/optimize',
        headers=headers,
        json={
            'route_name': 'Corruptable Route',
            'schedule_date': '2026-08-10',
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
            'vehicle_capacity_units': 200,
            'max_stops': 5,
            'persist_schedule': False,
        },
    )
    assert response.status_code == 200, response.text

    malformed = client.get('/api/v1/routes/history/not-a-uuid', headers=headers)
    assert malformed.status_code == 422

    run = db_session.execute(select(RouteOptimizationRun)).scalars().one()
    run.explanation_json = {'method': 1, 'summary': None}
    db_session.commit()

    corrupt = client.get(f'/api/v1/routes/history/{run.id}', headers=headers)
    assert corrupt.status_code == 422, corrupt.text
    assert corrupt.json()['detail'] == 'Stored route explanation is invalid'
