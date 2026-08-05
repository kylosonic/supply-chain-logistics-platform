"""Phase 4 banner-state tests (blueprint §10.2 — test_activation_banner_state.py, NB-26 + NB-34).

The server payload drives the banner copy matrix (decision #8); exact
copy strings are rendered console-side and asserted in the console test.
The state fields asserted here ARE the copy inputs: n_of_5, pct_complete,
next_step, cta, demo_mode, m6_completed.
"""

from tests.conftest import (
    real_fleet_csv,
    real_inventory_csv,
    real_items_csv,
    real_orders_csv,
    real_warehouse_csv,
)

_OPTIMIZE = {
    'route_name': 'Banner Route',
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


def _activation(client, token: str) -> dict:
    resp = client.get('/api/v1/activation', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _upload_prefix(client, token, upload_csv, count: int):
    specs = [
        ('warehouses', real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ])),
        ('items', real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)])),
        ('fleet', real_fleet_csv([('TRUCK-REAL-1', 'Real Driver', 40)])),
        ('inventory', real_inventory_csv([('WH-REAL-1', 'SKU-REAL-1', 100, 10)])),
        ('orders', real_orders_csv([('2026-08-01', 'WH-REAL-1', 'SKU-REAL-1', 10, 42.0, 'North')])),
    ]
    for category, content in specs[:count]:
        resp = upload_csv(token, category, content=content)
        assert resp.status_code == 200, resp.text


def test_banner_visible_at_signup_not_dismissible(client, signup_workspace, seed_csv_path):
    """NB-26.2: no dismiss endpoint exists for the activation banner."""
    _, token = signup_workspace()
    state = _activation(client, token)
    assert state['banner']['visible'] is True

    resp = client.post(
        '/api/v1/activation/pitch-dismiss', headers={'Authorization': f'Bearer {token}'},
        json={'level': 'p60'},
    )
    assert resp.status_code == 404  # nothing to dismiss — banner not dismissible


def test_banner_copy_zero_of_five(client, signup_workspace, seed_csv_path):
    """NB-34.5 copy inputs: 0% / 5 steps remaining / CTA /upload."""
    _, token = signup_workspace()
    state = _activation(client, token)

    assert state['n_of_5'] == 0
    assert state['pct_complete'] == 0
    assert state['next_step']['category'] == 'warehouses'
    assert state['banner']['cta'] == '/upload'
    assert state['banner']['demo_mode'] is True


def test_banner_copy_n_of_five_with_next_step(client, signup_workspace, seed_csv_path, upload_csv):
    """NB-34.4 copy inputs: N=2 -> 40% + 'Fleet Assets' next."""
    _, token = signup_workspace()
    _upload_prefix(client, token, upload_csv, 2)

    state = _activation(client, token)
    assert state['n_of_5'] == 2
    assert state['pct_complete'] == 40
    assert state['next_step'] == {'category': 'fleet_assets', 'label': 'Fleet Assets', 'cta': '/upload'}
    assert state['banner']['cta'] == '/upload'


def test_banner_copy_five_of_five_pre_optimization(client, signup_workspace, seed_csv_path, upload_csv):
    """NB-34.3 copy inputs: 80% + /routes CTA."""
    _, token = signup_workspace()
    _upload_prefix(client, token, upload_csv, 5)

    state = _activation(client, token)
    assert state['n_of_5'] == 5
    assert state['pct_complete'] == 80
    assert state['next_step'] is None
    assert state['banner']['cta'] == '/routes'
    assert state['banner']['demo_mode'] is False


def test_banner_copy_disappears_at_m6(client, signup_workspace, seed_csv_path):
    """NB-34.2: m6 -> no activation banner at all."""
    _, token = signup_workspace()
    resp = client.post(
        '/api/v1/routes/optimize', headers={'Authorization': f'Bearer {token}'}, json=_OPTIMIZE
    )
    assert resp.status_code == 200, resp.text

    state = _activation(client, token)
    assert state['m6_completed'] is True
    assert state['banner']['visible'] is False
    assert state['banner']['cta'] is None


def test_demo_messaging_absent_at_five_of_five(client, signup_workspace, seed_csv_path, upload_csv):
    """Decision #8: demo_mode False at 5-of-5 — demo messaging disappears,
    the onboarding banner persists until m6."""
    _, token = signup_workspace()
    _upload_prefix(client, token, upload_csv, 5)

    state = _activation(client, token)
    assert state['banner']['demo_mode'] is False
    assert state['banner']['visible'] is True


def test_banner_state_matches_milestone_counts(client, signup_workspace, seed_csv_path, upload_csv):
    _, token = signup_workspace()
    _upload_prefix(client, token, upload_csv, 3)

    state = _activation(client, token)
    assert state['banner']['n_of_5'] == state['n_of_5'] == 3
    completed = [m for m in state['milestones'] if m['completed']]
    assert [m['category'] for m in completed] == ['warehouses', 'items', 'fleet_assets']
    # Dangling sample inventory/orders were removed with the warehouses
    # supersede (decision #3) — 'empty' until that category turns real.
    assert state['milestones'][3]['status'] == 'empty'
