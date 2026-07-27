from fastapi.testclient import TestClient


def test_websocket_live_rejects_missing_token(client: TestClient):
    with client.websocket_connect('/api/v1/live/updates') as ws:
        ws.send_json({'type': 'auth'})
        data = ws.receive()
        assert data['type'] == 'websocket.close'


def test_websocket_live_accepts_token_and_streams_snapshot(client: TestClient, admin_token: str):
    with client.websocket_connect('/api/v1/live/updates') as ws:
        ws.send_json({'type': 'auth', 'token': admin_token})
        payload = ws.receive_json()
        assert payload['type'] == 'live_update'
        assert 'inventory_overview' in payload
        assert 'route_summaries' in payload
        assert 'forecast_preview' in payload
