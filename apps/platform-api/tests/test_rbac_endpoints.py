from fastapi.testclient import TestClient


def test_viewer_cannot_create_warehouse(client: TestClient, viewer_token: str):
    payload = {
        'code': 'WH-T1',
        'name': 'Test WH',
        'address': 'Addr',
        'city': 'City',
        'state': 'State',
        'country': 'ET',
        'latitude': 8.98,
        'longitude': 38.75,
        'capacity_units': 1000,
    }
    resp = client.post('/api/v1/warehouses', json=payload, headers={'Authorization': f'Bearer {viewer_token}'})
    assert resp.status_code == 403


def test_operator_can_create_warehouse(client: TestClient, operator_token: str):
    payload = {
        'code': 'WH-T2',
        'name': 'Operator WH',
        'address': 'Addr',
        'city': 'City',
        'state': 'State',
        'country': 'ET',
        'latitude': 8.99,
        'longitude': 38.76,
        'capacity_units': 1200,
    }
    resp = client.post('/api/v1/warehouses', json=payload, headers={'Authorization': f'Bearer {operator_token}'})
    assert resp.status_code == 201


def test_missing_token_rejected(client: TestClient):
    resp = client.get('/api/v1/warehouses')
    assert resp.status_code == 401
