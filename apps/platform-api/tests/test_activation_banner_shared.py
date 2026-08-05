"""Phase 4 shared-banner tests (blueprint §10.2 — test_activation_banner_shared.py, NB-30).

One state source drives both console render densities; state changes
reflect on the next read without reload (react-query invalidation is
asserted in the console tests); per-category origin chips (NB-30.5).
"""

from tests.conftest import real_fleet_csv, real_items_csv, real_warehouse_csv


def _activation(client, token: str) -> dict:
    resp = client.get('/api/v1/activation', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_activation_payload_single_source(
    client, db_session, signup_workspace, seed_csv_path
):
    """NB-30.1: one payload — banner, milestones, free_cap, pitch, toast."""
    from datetime import UTC, datetime
    from uuid import UUID

    from app.models.organization import Organization
    from app.services.activation import activation_banner_payload

    org_id, token = signup_workspace()

    state = _activation(client, token)
    assert set(state.keys()) == {
        'organization_id',
        'n_of_5',
        'pct_complete',
        'milestones',
        'm6_completed',
        'm6_completed_at',
        'next_step',
        'banner',
        'free_cap',
        'pitch',
        'toast_fired',
    }
    assert set(state['banner'].keys()) == {'visible', 'n_of_5', 'pct_complete', 'cta', 'demo_mode'}
    assert set(state['free_cap'].keys()) == {'locked', 'utilization_pct', 'message'}
    assert set(state['pitch'].keys()) == {'banner', 'dismissible', 'fired'}

    # banner.py single-source helper exposes the same state shape
    # (the console renders from GET /activation; the helper is the
    # NB-30.1 single-source contract used by both pages).
    org = db_session.get(Organization, UUID(org_id))
    banner = activation_banner_payload(db_session, org, datetime.now(UTC))
    assert banner['visible'] == state['banner']['visible']
    assert banner['n_of_5'] == state['banner']['n_of_5']
    assert banner['cta'] == state['banner']['cta']
    assert banner['demo_mode'] == state['banner']['demo_mode']
    assert banner['free_cap'] == state['free_cap']
    assert banner['pitch'] == state['pitch']
    assert banner['toast_fired'] == state['toast_fired']


def test_state_change_reflects_without_reload(client, signup_workspace, seed_csv_path, upload_csv):
    """NB-30.4: upload -> next GET returns the updated n_of_5 (the console
    invalidates ['activation'] after mutations — console test asserts it)."""
    _, token = signup_workspace()
    assert _activation(client, token)['n_of_5'] == 0

    upload_csv(
        token, 'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert _activation(client, token)['n_of_5'] == 1

    upload_csv(
        token, 'items',
        content=real_items_csv([('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2)]),
    )
    state = _activation(client, token)
    assert state['n_of_5'] == 2
    assert state['banner']['n_of_5'] == 2


def test_upload_page_reports_per_category_origin_chips(client, signup_workspace, seed_csv_path, upload_csv):
    """NB-30.5: real/sample/empty status per category after partial upload."""
    _, token = signup_workspace()

    upload_csv(
        token, 'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    upload_csv(
        token, 'fleet',
        content=real_fleet_csv([('TRUCK-REAL-1', 'Real Driver', 40)]),
    )

    state = _activation(client, token)
    statuses = {m['category']: m['status'] for m in state['milestones']}
    assert statuses['warehouses'] == 'real'
    assert statuses['fleet_assets'] == 'real'
    assert statuses['items'] == 'sample'
    # The warehouses supersede also removed the dangling sample inventory
    # and orders rows (decision #3) — they read as 'empty' until uploaded.
    assert statuses['inventory'] == 'empty'
    assert statuses['orders'] == 'empty'

    # n_of_5 stays sequential: only the warehouses prefix counts.
    assert state['n_of_5'] == 1
