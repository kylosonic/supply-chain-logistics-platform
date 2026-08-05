"""Phase 4 workspace-reset tests (blueprint §10.2 — test_activation_reset.py, NB-35).

Admin-gated, typed-confirmation reset: wipes real rows, re-seeds sample,
resets derived + stored activation state, clears pitch crossings, audits
with the admin user + timestamp.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.threshold_crossing import ThresholdCrossing
from app.models.user import User
from app.models.warehouse import Warehouse
from tests.conftest import (
    real_fleet_csv,
    real_inventory_csv,
    real_items_csv,
    real_orders_csv,
    real_warehouse_csv,
)

_OPTIMIZE = {
    'route_name': 'Reset Route',
    'schedule_date': '2026-08-10',
    'start_warehouse_code': 'WH-001',
    'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
    'vehicle_capacity_units': 100,
    'max_stops': 5,
    'speed_kmh': 45,
    'cost_per_km': 1.5,
    'persist_schedule': False,
    'minimize_carbon_footprint': False,
}


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _activation(client, token: str) -> dict:
    resp = client.get('/api/v1/activation', headers=_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


def _reset(client, token: str, name: str):
    return client.post('/api/v1/activation/reset', headers=_headers(token), json={'workspace_name': name})


def _upload_all_five(client, token, upload_csv):
    upload_csv(
        token, 'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    upload_csv(
        token, 'items',
        content=real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)]),
    )
    upload_csv(token, 'fleet', content=real_fleet_csv([('TRUCK-REAL-1', 'Real Driver', 40)]))
    upload_csv(token, 'inventory', content=real_inventory_csv([('WH-REAL-1', 'SKU-REAL-1', 100, 10)]))
    upload_csv(
        token, 'orders',
        content=real_orders_csv([('2026-08-01', 'WH-REAL-1', 'SKU-REAL-1', 10, 42.0, 'North')]),
    )


def test_reset_requires_admin_role(client, db_session: Session, signup_workspace, seed_csv_path):
    """Operator membership -> 403; owner -> 200."""
    org_id, owner_token = signup_workspace(name='Reset Co')

    operator = db_session.execute(
        select(User).where(User.username == 'operator')
    ).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=UUID(org_id), user_id=operator.id, role='operator', is_active=True
        )
    )
    db_session.commit()

    resp = client.post('/api/v1/auth/login', json={'username': 'operator', 'password': 'operator12345'})
    operator_token = resp.json()['access_token']

    blocked = _reset(client, operator_token, 'Reset Co')
    assert blocked.status_code == 403

    ok = _reset(client, owner_token, 'Reset Co')
    assert ok.status_code == 200, ok.text
    assert ok.json()['activation_reset'] is True
    assert set(ok.json()['rows_reseeded'].keys()) == {
        'warehouses', 'items', 'fleet_assets', 'inventory', 'orders'
    }


def test_reset_requires_exact_workspace_name(client, signup_workspace, seed_csv_path):
    org_id, token = signup_workspace(name='Exact Reset Co')

    mismatch = _reset(client, token, 'wrong name')
    assert mismatch.status_code == 422

    case_mismatch = _reset(client, token, 'exact reset co')
    assert case_mismatch.status_code == 422

    padded = _reset(client, token, '  Exact Reset Co  ')
    assert padded.status_code == 200, padded.text

    empty = client.post(
        '/api/v1/activation/reset', headers=_headers(token), json={'workspace_name': '   '}
    )
    assert empty.status_code == 422


def test_reset_wipes_real_uploads_and_reseeds_sample(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv, sample_row_counts
):
    org_id, token = signup_workspace(name='Wipe Co')
    _upload_all_five(client, token, upload_csv)

    real_warehouse = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_id), Warehouse.data_origin == 'real'
        )
    ).scalars().all()
    assert len(real_warehouse) == 1

    resp = _reset(client, token, 'Wipe Co')
    assert resp.status_code == 200, resp.text

    real_left = db_session.execute(
        select(func.count()).select_from(Warehouse).where(
            Warehouse.organization_id == UUID(org_id), Warehouse.data_origin == 'real'
        )
    ).scalar_one()
    assert real_left == 0

    counts = sample_row_counts(org_id)
    for category in ('warehouses', 'items', 'fleet_assets', 'inventory', 'orders'):
        assert counts[category] > 0


def test_reset_milestones_back_to_zero(client, signup_workspace, seed_csv_path, upload_csv):
    """Decision #1 derived semantics: reset -> n_of_5 0, m6 cleared."""
    _, token = signup_workspace(name='Zero Co')

    # m6 first (sample substrate), then all 5 real uploads.
    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 200, resp.text
    assert resp.json()['post_aha_toast'] is True
    _upload_all_five(client, token, upload_csv)

    state = _activation(client, token)
    assert state['n_of_5'] == 5
    assert state['m6_completed'] is True

    resp = _reset(client, token, 'Zero Co')
    assert resp.status_code == 200, resp.text

    state = _activation(client, token)
    assert state['n_of_5'] == 0
    assert state['pct_complete'] == 0
    assert state['m6_completed'] is False
    assert state['toast_fired'] is False
    assert state['banner']['visible'] is True


def test_reset_clears_pitch_crossings(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage
):
    org_id, token = signup_workspace(name='Crossings Co')
    advance_usage(org_id, 'delivery_tasks', 1500)

    assert _activation(client, token)['pitch']['banner'] == 'p60'
    rows = db_session.execute(
        select(ThresholdCrossing).where(ThresholdCrossing.organization_id == UUID(org_id))
    ).scalars().all()
    assert len(rows) == 1

    resp = _reset(client, token, 'Crossings Co')
    assert resp.status_code == 200, resp.text

    rows = db_session.execute(
        select(ThresholdCrossing).where(ThresholdCrossing.organization_id == UUID(org_id))
    ).scalars().all()
    assert rows == []


def test_reset_audit_event_with_admin_and_timestamp(
    client, db_session: Session, signup_workspace, seed_csv_path
):
    """NB-35.5: workspace.reset_to_sample_data with admin user + timestamp."""
    org_id, token = signup_workspace(name='Audit Reset Co')

    resp = _reset(client, token, 'Audit Reset Co')
    assert resp.status_code == 200, resp.text

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'workspace.reset_to_sample_data')
    ).scalars().first()
    assert event is not None
    assert event.organization_id == UUID(org_id)
    assert event.actor_user_id is not None
    assert event.created_at is not None
    assert event.payload['workspace_name'] == 'Audit Reset Co'
    assert sorted(event.payload['categories']) == [
        'fleet_assets', 'inventory', 'items', 'orders', 'warehouses'
    ]
    assert event.payload['rows_reseeded']['warehouses'] > 0
