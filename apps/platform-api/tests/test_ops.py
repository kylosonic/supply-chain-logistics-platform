from fastapi.testclient import TestClient


def test_readiness_endpoint_ok(client: TestClient):
    resp = client.get('/api/v1/ops/ready')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_metrics_requires_auth(client: TestClient):
    resp = client.get('/api/v1/ops/metrics')
    assert resp.status_code == 401


def test_metrics_forbidden_for_viewer(client: TestClient, viewer_token: str):
    resp = client.get('/api/v1/ops/metrics', headers={'Authorization': f'Bearer {viewer_token}'})
    assert resp.status_code == 403


def test_metrics_accessible_for_admin(client: TestClient, admin_token: str):
    resp = client.get('/api/v1/ops/metrics', headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 200
    payload = resp.json()
    assert 'requests_total' in payload
    assert 'websocket_connections' in payload
