"""Phase 4 milestone tests (blueprint §10.2 — test_activation_milestones.py, NB-28).

Derived milestones 1-5 (real-row presence, sequential prefix rule) and
stored milestone 6 (first route optimization, ANY substrate). State is
per-organization, shared by every member.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import OrganizationMembership
from app.models.user import User
from tests.conftest import (
    real_fleet_csv,
    real_inventory_csv,
    real_items_csv,
    real_orders_csv,
    real_warehouse_csv,
)

_OPTIMIZE = {
    'route_name': 'Milestone Route',
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


def _activation(client, token, org_id: str | None = None) -> dict:
    headers = {'Authorization': f'Bearer {token}'}
    if org_id:
        headers['X-Organization-Id'] = org_id
    resp = client.get('/api/v1/activation', headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_fresh_signup_is_zero_of_five(client, signup_workspace, seed_csv_path):
    _, token = signup_workspace()
    state = _activation(client, token)

    assert state['n_of_5'] == 0
    assert state['pct_complete'] == 0
    assert state['m6_completed'] is False
    assert state['toast_fired'] is False
    assert state['next_step']['category'] == 'warehouses'
    assert state['banner']['visible'] is True
    assert state['banner']['cta'] == '/upload'
    assert state['banner']['demo_mode'] is True

    for milestone in state['milestones']:
        assert milestone['status'] == 'sample'
        assert milestone['completed'] is False
        assert milestone['real_rows'] == 0
        assert milestone['sample_rows'] > 0


def test_upload_orders_only_registers_zero(client, signup_workspace, seed_csv_path, upload_csv):
    """Sequential prefix rule: out-of-order uploads do not register."""
    _, token = signup_workspace()
    resp = upload_csv(
        token,
        'orders',
        content=real_orders_csv([
            ('2026-08-01', 'WH-001', 'SKU-001', 10, 42.0, 'North'),
        ]),
    )
    assert resp.status_code == 200, resp.text

    state = _activation(client, token)
    assert state['n_of_5'] == 0
    orders_milestone = next(m for m in state['milestones'] if m['category'] == 'orders')
    assert orders_milestone['status'] == 'real'
    assert orders_milestone['completed'] is False
    assert state['next_step']['category'] == 'warehouses'


def test_upload_warehouses_then_items_advances_two(client, signup_workspace, seed_csv_path, upload_csv):
    _, token = signup_workspace()

    resp = upload_csv(
        token,
        'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert resp.status_code == 200, resp.text
    state = _activation(client, token)
    assert state['n_of_5'] == 1
    assert state['pct_complete'] == 20
    assert state['next_step']['category'] == 'items'

    resp = upload_csv(
        token,
        'items',
        content=real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)]),
    )
    assert resp.status_code == 200, resp.text
    state = _activation(client, token)
    assert state['n_of_5'] == 2
    assert state['pct_complete'] == 40
    assert state['next_step']['category'] == 'fleet_assets'
    assert state['banner']['cta'] == '/upload'
    assert state['banner']['demo_mode'] is True


def test_milestone_4_and_5_sequential_order(client, signup_workspace, seed_csv_path, upload_csv):
    _, token = signup_workspace()

    uploads = [
        (
            'warehouses',
            real_warehouse_csv([('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100)]),
        ),
        ('items', real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)])),
        ('fleet', real_fleet_csv([('TRUCK-REAL-1', 'Real Driver', 40)])),
        ('inventory', real_inventory_csv([('WH-REAL-1', 'SKU-REAL-1', 100, 10)])),
    ]
    for category, content in uploads:
        resp = upload_csv(token, category, content=content)
        assert resp.status_code == 200, resp.text

    state = _activation(client, token)
    assert state['n_of_5'] == 4
    assert state['pct_complete'] == 80
    assert state['next_step']['category'] == 'orders'
    assert state['banner']['cta'] == '/upload'
    assert state['banner']['demo_mode'] is True

    resp = upload_csv(
        token,
        'orders',
        content=real_orders_csv([
            ('2026-08-01', 'WH-REAL-1', 'SKU-REAL-1', 10, 42.0, 'North'),
        ]),
    )
    assert resp.status_code == 200, resp.text

    state = _activation(client, token)
    assert state['n_of_5'] == 5
    assert state['pct_complete'] == 80
    assert state['next_step'] is None
    assert state['banner']['cta'] == '/routes'
    assert state['banner']['demo_mode'] is False


def test_m6_on_sample_data_registers(client, signup_workspace, seed_csv_path):
    """NB-28.4: milestone 6 reachable at 0-of-5 on full-sample data."""
    _, token = signup_workspace()

    state = _activation(client, token)
    assert state['n_of_5'] == 0
    assert state['m6_completed'] is False

    resp = client.post(
        '/api/v1/routes/optimize', headers={'Authorization': f'Bearer {token}'}, json=_OPTIMIZE
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['post_aha_toast'] is True
    assert resp.json()['data_origin'] == 'sample'

    state = _activation(client, token)
    assert state['m6_completed'] is True
    assert state['m6_completed_at'] is not None
    assert state['toast_fired'] is True


def test_m6_first_run_any_substrate(client, signup_workspace, seed_csv_path, upload_csv):
    """Decision #7: no prefix requirement — optimize at 0-of-5 registers m6."""
    _, token = signup_workspace()

    resp = client.post(
        '/api/v1/routes/optimize', headers={'Authorization': f'Bearer {token}'}, json=_OPTIMIZE
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['post_aha_toast'] is True

    state = _activation(client, token)
    assert state['m6_completed'] is True
    # banner disappears entirely at m6 (decision #8)
    assert state['banner']['visible'] is False


def test_m6_does_not_require_prefix(client, signup_workspace, seed_csv_path):
    """NB-28.4 wins over the sequential prose: m6 with n_of_5 == 0."""
    _, token = signup_workspace()
    state = _activation(client, token)
    assert state['n_of_5'] == 0

    resp = client.post(
        '/api/v1/routes/optimize', headers={'Authorization': f'Bearer {token}'}, json=_OPTIMIZE
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['post_aha_toast'] is True

    state = _activation(client, token)
    assert state['n_of_5'] == 0
    assert state['m6_completed'] is True


def test_state_per_organization_not_per_user(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """NB-28.2: two members of the same org share one activation state."""
    org_id, owner_token = signup_workspace()

    operator = db_session.execute(
        select(User).where(User.username == 'operator')
    ).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=UUID(org_id), user_id=operator.id, role='operator', is_active=True
        )
    )
    db_session.commit()

    resp = upload_csv(
        owner_token,
        'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert resp.status_code == 200, resp.text

    resp = client.post('/api/v1/auth/login', json={'username': 'operator', 'password': 'operator12345'})
    assert resp.status_code == 200
    operator_token = resp.json()['access_token']

    owner_state = _activation(client, owner_token, org_id)
    operator_state = _activation(client, operator_token, org_id)
    assert owner_state['n_of_5'] == operator_state['n_of_5'] == 1
    assert owner_state['next_step'] == operator_state['next_step']


def test_second_user_inherits_state(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """NB-9.2-style: a joining user sees the same checklist as teammates."""
    org_id, owner_token = signup_workspace()

    for category, content in [
        (
            'warehouses',
            real_warehouse_csv([('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100)]),
        ),
        ('items', real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)])),
    ]:
        resp = upload_csv(owner_token, category, content=content)
        assert resp.status_code == 200, resp.text

    viewer = db_session.execute(select(User).where(User.username == 'viewer')).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=UUID(org_id), user_id=viewer.id, role='viewer', is_active=True
        )
    )
    db_session.commit()

    resp = client.post('/api/v1/auth/login', json={'username': 'viewer', 'password': 'viewer12345'})
    assert resp.status_code == 200
    viewer_token = resp.json()['access_token']

    state = _activation(client, viewer_token, org_id)
    assert state['n_of_5'] == 2
    assert state['next_step']['category'] == 'fleet_assets'
    warehouses = next(m for m in state['milestones'] if m['category'] == 'warehouses')
    assert warehouses['completed'] is True
