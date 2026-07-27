from fastapi.testclient import TestClient


def _signup_company(client: TestClient, *, tier: str = 'starter', suffix: str = '1') -> str:
    resp = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': f'Metering Co {suffix}',
            'company_email': f'owner{suffix}@meteringco.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': tier,
        },
    )
    assert resp.status_code == 201
    return resp.json()['access_token']


def test_usage_metering_emits_threshold_events(client: TestClient):
    token = _signup_company(client, tier='starter', suffix='threshold')
    auth = {'Authorization': f'Bearer {token}'}

    first = client.post('/api/v1/subscriptions/usage/record', headers=auth, json={'units': 1800})
    assert first.status_code == 200
    assert first.json()['events'] == []

    approaching = client.post('/api/v1/subscriptions/usage/record', headers=auth, json={'units': 300})
    assert approaching.status_code == 200
    approaching_levels = [event['level'] for event in approaching.json()['events']]
    assert 'approaching_limit' in approaching_levels

    reached = client.post('/api/v1/subscriptions/usage/record', headers=auth, json={'units': 400})
    assert reached.status_code == 200
    reached_levels = [event['level'] for event in reached.json()['events']]
    assert 'limit_reached' in reached_levels

    overage = client.post('/api/v1/subscriptions/usage/record', headers=auth, json={'units': 50})
    assert overage.status_code == 200
    overage_levels = [event['level'] for event in overage.json()['events']]
    assert 'overage' in overage_levels

    usage = client.get('/api/v1/subscriptions/usage/me', headers=auth)
    assert usage.status_code == 200
    payload = usage.json()
    assert payload['metric'] == 'delivery_tasks'
    assert payload['included_units'] == 2500
    assert payload['used_units'] == 2550
    assert payload['overage_units'] == 50
    assert payload['estimated_overage_cost_usd'] == 10.0


def test_enterprise_usage_has_no_threshold_limit(client: TestClient):
    token = _signup_company(client, tier='enterprise', suffix='enterprise')
    auth = {'Authorization': f'Bearer {token}'}

    resp = client.post('/api/v1/subscriptions/usage/record', headers=auth, json={'units': 6000})
    assert resp.status_code == 200
    body = resp.json()
    assert body['events'] == []
    assert body['usage']['included_units'] is None
    assert body['usage']['utilization_percent'] is None
    assert body['usage']['estimated_overage_cost_usd'] is None


def test_usage_metering_requires_active_org_membership(client: TestClient, admin_token: str):
    resp = client.post(
        '/api/v1/subscriptions/usage/record',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'units': 25},
    )
    assert resp.status_code == 403
