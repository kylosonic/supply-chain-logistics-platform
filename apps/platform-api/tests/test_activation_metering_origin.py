"""Phase 4 metering-origin tests (blueprint §10.2 — test_activation_metering_origin.py, NB-27).

Both meters record per run; sample vs real substrate counts IDENTICALLY
(metering never differentiates); the substrate surfaces only in the audit
payload (decision #4); the upload audit gap-fill event.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.usage_meter import OrganizationUsageCounter
from tests.conftest import real_orders_csv, real_warehouse_csv

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
    'persist_schedule': False,
    'minimize_carbon_footprint': False,
}


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _counter(db: Session, org_id: str, metric: str) -> OrganizationUsageCounter | None:
    return db.execute(
        select(OrganizationUsageCounter).where(
            OrganizationUsageCounter.organization_id == UUID(org_id),
            OrganizationUsageCounter.metric == metric,
        )
    ).scalar_one_or_none()


def test_route_optimization_records_both_meters(
    client, db_session: Session, signup_workspace, seed_csv_path
):
    """Decision #12 gap-fill: route_optimizations = 1 per run, delivery_tasks
    = deliveries count (as before)."""
    org_id, token = signup_workspace()

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE_TWO)
    assert resp.status_code == 200, resp.text

    dt = _counter(db_session, org_id, 'delivery_tasks')
    ro = _counter(db_session, org_id, 'route_optimizations')
    assert dt is not None and dt.used_units == 2
    assert ro is not None and ro.used_units == 1


def test_sample_substrate_optimization_counts_identically(
    client, db_session: Session, signup_workspace, seed_csv_path
):
    """NB-27.1/2: sample-substrate runs consume identical meters."""
    org_id, token = signup_workspace()

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE_TWO)
    assert resp.status_code == 200, resp.text

    dt = _counter(db_session, org_id, 'delivery_tasks')
    ro = _counter(db_session, org_id, 'route_optimizations')
    assert (dt.used_units, ro.used_units) == (2, 1)


def test_route_audit_data_origin_real(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """All-real substrate -> route.optimized payload data_origin='real'."""
    _, token = signup_workspace()
    upload_csv(
        token, 'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH A', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
            ('WH-REAL-2', 'Real WH B', '2 Rd', 'Addis', 'AA', 'Ethiopia', 9.1, 38.8, 100),
        ]),
    )

    resp = client.post(
        '/api/v1/routes/optimize', headers=_headers(token),
        json={
            **_OPTIMIZE_TWO,
            'start_warehouse_code': 'WH-REAL-1',
            'deliveries': [{'warehouse_code': 'WH-REAL-2', 'demand_units': 10}],
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['data_origin'] == 'real'

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'route.optimized')
    ).scalars().first()
    assert event is not None
    assert event.payload['data_origin'] == 'real'
    assert event.payload['deliveries_count'] == 1


def test_route_audit_data_origin_sample(client, db_session: Session, signup_workspace, seed_csv_path):
    """Decision #4: a run touching ANY sample warehouse is sample-substrate."""
    _, token = signup_workspace()

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE_TWO)
    assert resp.status_code == 200, resp.text
    assert resp.json()['data_origin'] == 'sample'

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'route.optimized')
    ).scalars().first()
    assert event.payload['data_origin'] == 'sample'


def test_metering_never_stores_origin(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """NB-27.4: no data_origin anywhere on the counters; sample and real
    runs produce byte-identical counter rows."""
    columns = set(OrganizationUsageCounter.__table__.columns.keys())
    assert 'data_origin' not in columns

    org_a, token_a = signup_workspace(name='Origin A')
    org_b, token_b = signup_workspace(name='Origin B')

    # org_a: real substrate run; org_b: sample substrate run — IDENTICAL
    # run sizes so the counters must match exactly.
    upload_csv(
        token_a, 'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH A', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
            ('WH-REAL-2', 'Real WH B', '2 Rd', 'Addis', 'AA', 'Ethiopia', 9.1, 38.8, 100),
        ]),
    )
    single_delivery_real = {
        **_OPTIMIZE_TWO,
        'start_warehouse_code': 'WH-REAL-1',
        'deliveries': [{'warehouse_code': 'WH-REAL-2', 'demand_units': 10}],
    }
    single_delivery_sample = {
        **_OPTIMIZE_TWO,
        'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
    }
    client.post('/api/v1/routes/optimize', headers=_headers(token_a), json=single_delivery_real)
    client.post('/api/v1/routes/optimize', headers=_headers(token_b), json=single_delivery_sample)

    columns = set(OrganizationUsageCounter.__table__.columns.keys())
    assert 'data_origin' not in columns

    for metric in ('delivery_tasks', 'route_optimizations'):
        a = _counter(db_session, org_a, metric)
        b = _counter(db_session, org_b, metric)
        assert a.used_units == b.used_units
        assert a.period_start == b.period_start


def test_upload_audit_event_with_counts_and_origin(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """Decision #4 gap-fill: workspace.csv_uploaded with counts + origin."""
    _, token = signup_workspace()

    resp = upload_csv(
        token, 'orders',
        content=real_orders_csv([
            ('2026-08-01', 'WH-001', 'SKU-001', 10, 42.0, 'North'),
            ('2026-08-02', 'WH-002', 'SKU-002', 20, 20.0, 'East'),
        ]),
    )
    assert resp.status_code == 200, resp.text

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'workspace.csv_uploaded')
    ).scalars().first()
    assert event is not None
    assert event.payload['category'] == 'orders'
    assert event.payload['data_origin'] == 'real'
    assert event.payload['records_processed'] == 2
    assert event.payload['records_created'] == 2
    assert event.payload['records_updated'] == 0
    assert event.payload['errors'] == []
