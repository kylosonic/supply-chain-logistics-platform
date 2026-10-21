"""TECH-57 — org-scoped route optimization (blueprint §7.1).

Regression: POST /api/v1/routes/optimize with ``persist_schedule=true``
(the ops-console default) 500ed with MultipleResultsFound once 2+ orgs
held identical seeded codes (WH-001..003 per org). All four warehouse
queries in ``optimize_routes`` are org-scoped via
``resolve_actor_organization_id``. Business access now requires an active
organization membership, so an unaffiliated actor cannot reach this path.
"""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.route import RouteSchedule, RouteStop
from app.models.warehouse import Warehouse

_OPTIMIZE_TWO = {
    'route_name': 'Meter Route',
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
}


def _optimize_payload(**overrides: object) -> dict:
    payload = dict(_OPTIMIZE_TWO)
    payload.update(overrides)
    return payload


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _org_warehouse_ids(db: Session, org_id: str) -> dict[str, UUID]:
    rows = db.execute(
        select(Warehouse).where(Warehouse.organization_id == UUID(org_id))
    ).scalars().all()
    return {w.code: w.id for w in rows}


def test_optimize_persist_true_org_a_returns_200_and_schedule_under_org_a(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Org A')
    a_wh = _org_warehouse_ids(db_session, org_a)

    resp = client.post(
        '/api/v1/routes/optimize', headers=_headers(token_a), json=_optimize_payload()
    )
    assert resp.status_code == 200, resp.text

    schedules = db_session.execute(select(RouteSchedule)).scalars().all()
    assert len(schedules) == 1
    assert schedules[0].start_warehouse_id == a_wh['WH-001']

    stops = db_session.execute(
        select(RouteStop).where(RouteStop.route_schedule_id == schedules[0].id)
    ).scalars().all()
    assert {s.warehouse_id for s in stops} == {a_wh['WH-002'], a_wh['WH-003']}


def test_optimize_persist_true_org_b_returns_200_and_schedule_under_org_b(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    """Two orgs with identical seeded codes: each persist=true run lands
    its own schedule, each pointing at its own org's WH-001 (the P0:
    global scalar_one() previously 500ed with MultipleResultsFound)."""
    org_a, token_a = signup_workspace('Org A')
    org_b, token_b = signup_workspace('Org B')
    a_wh = _org_warehouse_ids(db_session, org_a)
    b_wh = _org_warehouse_ids(db_session, org_b)

    resp_a = client.post(
        '/api/v1/routes/optimize', headers=_headers(token_a), json=_optimize_payload()
    )
    assert resp_a.status_code == 200, resp_a.text
    resp_b = client.post(
        '/api/v1/routes/optimize', headers=_headers(token_b), json=_optimize_payload()
    )
    assert resp_b.status_code == 200, resp_b.text

    schedules = db_session.execute(select(RouteSchedule)).scalars().all()
    assert len(schedules) == 2
    starts = {s.start_warehouse_id for s in schedules}
    assert starts == {a_wh['WH-001'], b_wh['WH-001']}

    for schedule in schedules:
        stops = db_session.execute(
            select(RouteStop).where(RouteStop.route_schedule_id == schedule.id)
        ).scalars().all()
        stop_ids = {s.warehouse_id for s in stops}
        assert stop_ids == {a_wh['WH-002'], a_wh['WH-003']} or stop_ids == {
            b_wh['WH-002'],
            b_wh['WH-003'],
        }


def test_optimize_start_warehouse_from_other_org_returns_404(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    """B-only warehouse is invisible to A's optimize (nodes org-scoped):
    404 before any persistence — no RouteSchedule is created. The 201 also
    doubles as the TECH-58 create-stamps-org check."""
    org_a, token_a = signup_workspace('Org A')
    org_b, token_b = signup_workspace('Org B')

    create = client.post(
        '/api/v1/warehouses',
        headers=_headers(token_b),
        json={
            'code': 'WH-X1',
            'name': 'B Only WH',
            'address': 'Addr',
            'city': 'City',
            'state': 'State',
            'country': 'ET',
            'latitude': 9.1,
            'longitude': 38.8,
            'capacity_units': 100,
        },
    )
    assert create.status_code == 201, create.text
    b_row = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_b), Warehouse.code == 'WH-X1'
        )
    ).scalar_one()
    assert b_row.organization_id == UUID(org_b)

    resp = client.post(
        '/api/v1/routes/optimize',
        headers=_headers(token_a),
        json=_optimize_payload(start_warehouse_code='WH-X1'),
    )
    assert resp.status_code == 404
    assert resp.json()['detail'] == 'start_warehouse_code not found'
    assert db_session.execute(select(RouteSchedule)).scalars().all() == []


def test_single_org_optimize_persist_true_unchanged(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    """Fresh single org: persist=true still returns 200 with exactly one
    schedule under that org (pre-TECH-57 behavior preserved)."""
    org_c, token_c = signup_workspace('Org C')
    c_wh = _org_warehouse_ids(db_session, org_c)

    resp = client.post(
        '/api/v1/routes/optimize', headers=_headers(token_c), json=_optimize_payload()
    )
    assert resp.status_code == 200, resp.text

    schedules = db_session.execute(select(RouteSchedule)).scalars().all()
    assert len(schedules) == 1
    assert schedules[0].start_warehouse_id == c_wh['WH-001']
