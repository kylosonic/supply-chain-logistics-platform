"""Phase 4 panel-gating tests (blueprint §10.2 — test_activation_panel_gating.py, NB-29).

Server-side assertions of the state the console gates on: milestone
boundaries m4/m5/m6 map to the reveal thresholds; always-visible
surfaces (banner/exception/audit/feedback) exist at milestone 0; the
progression is sequential and immutable (no per-panel config path).
"""

from tests.conftest import (
    real_fleet_csv,
    real_inventory_csv,
    real_items_csv,
    real_orders_csv,
    real_warehouse_csv,
)

_OPTIMIZE = {
    'route_name': 'Panel Route',
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
            ('WH-REAL-2', 'Real WH 2', '2 Rd', 'Addis', 'AA', 'Ethiopia', 9.1, 38.8, 100),
        ])),
        ('items', real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)])),
        ('fleet', real_fleet_csv([('TRUCK-REAL-1', 'Real Driver', 40)])),
        ('inventory', real_inventory_csv([('WH-REAL-1', 'SKU-REAL-1', 100, 10)])),
        ('orders', real_orders_csv([('2026-08-01', 'WH-REAL-1', 'SKU-REAL-1', 10, 42.0, 'North')])),
    ]
    for category, content in specs[:count]:
        resp = upload_csv(token, category, content=content)
        assert resp.status_code == 200, resp.text


def test_panel_gate_payload_milestone_mapping(client, signup_workspace, seed_csv_path, upload_csv):
    """NB-29.1 state mapping: m4 -> n_of_5 4; m5 -> 5; m6 -> m6_completed."""
    _, token = signup_workspace()

    _upload_prefix(client, token, upload_csv, 4)
    state = _activation(client, token)
    assert state['n_of_5'] == 4
    assert state['m6_completed'] is False

    _upload_prefix(client, token, upload_csv, 5)
    state = _activation(client, token)
    assert state['n_of_5'] == 5
    assert state['m6_completed'] is False

    resp = client.post(
        '/api/v1/routes/optimize', headers={'Authorization': f'Bearer {token}'},
        json={**_OPTIMIZE, 'start_warehouse_code': 'WH-REAL-1',
              'deliveries': [{'warehouse_code': 'WH-REAL-2', 'demand_units': 10}]},
    )
    assert resp.status_code == 200, resp.text
    state = _activation(client, token)
    assert state['m6_completed'] is True


def test_always_visible_surfaces_flagged(client, signup_workspace, seed_csv_path):
    """NB-29.2: the always-visible surfaces exist at milestone 0 — the
    banner payload is present, and the exception/audit/feedback surfaces
    are unguarded reads (200 from signup)."""
    _, token = signup_workspace()

    state = _activation(client, token)
    assert state['banner']['visible'] is True
    assert state['n_of_5'] == 0

    headers = {'Authorization': f'Bearer {token}'}
    feed = client.get('/api/v1/ops/exception-feed', headers=headers)
    assert feed.status_code == 200
    audit = client.get('/api/v1/ops/audit-timeline', headers=headers)
    assert audit.status_code == 200
    # The feedback surface is a console form (asserted in the console
    # smoke test); the server-side always-visible set is banner + feed +
    # audit, all present at milestone 0.


def test_gating_order_immutable(client, signup_workspace, seed_csv_path, upload_csv):
    """NB-29.4: the reveal sequence is fixed — out-of-order uploads never
    advance past the sequential prefix."""
    _, token = signup_workspace()

    # Upload orders FIRST (out of order) then warehouses+items.
    upload_csv(
        token, 'orders',
        content=real_orders_csv([('2026-08-01', 'WH-001', 'SKU-001', 10, 42.0, 'North')]),
    )
    state = _activation(client, token)
    assert state['n_of_5'] == 0

    _upload_prefix(client, token, upload_csv, 2)
    state = _activation(client, token)
    assert state['n_of_5'] == 2
    assert [m['category'] for m in state['milestones'] if m['completed']] == [
        'warehouses', 'items'
    ]
