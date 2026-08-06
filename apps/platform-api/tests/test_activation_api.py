"""Phase 4 activation API tests (blueprint §10.2 — test_activation_api.py).

Route registration, auth gating, payload shape, pitch-dismiss validation,
reset route presence.
"""


def _headers(token: str | None = None) -> dict:
    return {'Authorization': f'Bearer {token}'} if token else {}


def test_get_activation_membership_required(client, signup_workspace, seed_csv_path):
    resp = client.get('/api/v1/activation')
    assert resp.status_code == 401


def test_get_activation_full_payload_shape(client, signup_workspace, seed_csv_path):
    _, token = signup_workspace()
    resp = client.get('/api/v1/activation', headers=_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body['organization_id']
    assert body['n_of_5'] == 0
    assert body['pct_complete'] == 0
    assert isinstance(body['milestones'], list) and len(body['milestones']) == 5
    assert body['m6_completed'] is False
    assert body['m6_completed_at'] is None
    assert body['next_step']['category'] == 'warehouses'
    assert body['banner']['visible'] is True
    assert body['free_cap']['locked'] is False
    assert body['pitch']['banner'] is None
    assert body['toast_fired'] is False


def test_pitch_dismiss_unknown_level_422(client, signup_workspace, seed_csv_path, advance_usage):
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 1500)
    client.get('/api/v1/activation', headers=_headers(token))

    resp = client.post(
        '/api/v1/activation/pitch-dismiss', headers=_headers(token), json={'level': 'p80'}
    )
    assert resp.status_code == 422

    resp = client.post(
        '/api/v1/activation/pitch-dismiss', headers=_headers(token), json={'level': 'p60'}
    )
    assert resp.status_code == 200
    assert resp.json() == {'dismissed': True}


def test_pitch_dismiss_missing_crossing_404(client, signup_workspace, seed_csv_path):
    _, token = signup_workspace()
    resp = client.post(
        '/api/v1/activation/pitch-dismiss', headers=_headers(token), json={'level': 'p60'}
    )
    assert resp.status_code == 404


def test_reset_endpoint_route_registered(client, signup_workspace, seed_csv_path):
    org_id, token = signup_workspace(name='Route Co')
    resp = client.post(
        '/api/v1/activation/reset', headers=_headers(token), json={'workspace_name': 'Route Co'}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['activation_reset'] is True
