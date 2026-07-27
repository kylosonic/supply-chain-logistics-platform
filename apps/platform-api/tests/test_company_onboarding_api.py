from fastapi.testclient import TestClient


def test_company_signup_and_onboarding_flow(client: TestClient):
    signup = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': 'Acme Logistics',
            'company_email': 'owner@acme-logistics.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Acme Owner',
            'subscription_tier': 'scale',
        },
    )
    assert signup.status_code == 201
    payload = signup.json()
    assert payload['organization']['name'] == 'Acme Logistics'
    assert payload['organization']['subscription_tier'] == 'scale'

    token = payload['access_token']
    auth = {'Authorization': f'Bearer {token}'}

    subscription_me = client.get('/api/v1/subscriptions/me', headers=auth)
    assert subscription_me.status_code == 200
    assert subscription_me.json()['tier'] == 'scale'

    select_tier = client.post('/api/v1/subscriptions/select-tier', headers=auth, json={'tier': 'enterprise'})
    assert select_tier.status_code == 200
    assert select_tier.json()['tier'] == 'enterprise'
    assert select_tier.json()['status'] == 'active'

    create_key = client.post(
        '/api/v1/providers/keys',
        headers=auth,
        json={'provider_name': 'openai', 'key_name': 'primary', 'api_key': 'sk-test-this-is-a-long-secret-key'},
    )
    assert create_key.status_code == 201
    key_payload = create_key.json()
    assert key_payload['provider_name'] == 'openai'
    assert key_payload['status'] == 'active'

    key_id = key_payload['id']

    key_list = client.get('/api/v1/providers/keys', headers=auth)
    assert key_list.status_code == 200
    assert any(item['id'] == key_id for item in key_list.json())

    key_test = client.post(f'/api/v1/providers/keys/{key_id}/test', headers=auth)
    assert key_test.status_code == 200
    assert key_test.json()['ok'] is True

    set_preference = client.post('/api/v1/providers/preference', headers=auth, json={'key_id': key_id})
    assert set_preference.status_code == 200
    assert set_preference.json()['provider_name'] == 'openai'

    get_preference = client.get('/api/v1/providers/preference', headers=auth)
    assert get_preference.status_code == 200
    assert get_preference.json()['key_id'] == key_id

    revoke = client.post(f'/api/v1/providers/keys/{key_id}/revoke', headers=auth, json={})
    assert revoke.status_code == 200
    assert revoke.json()['status'] == 'revoked'


def test_company_signup_rejects_public_email_domains(client: TestClient):
    signup = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': 'Public Mail Co',
            'company_email': 'owner@gmail.com',
            'password': 'VeryStrongPass9',
            'subscription_tier': 'starter',
        },
    )
    assert signup.status_code == 400


def test_login_with_email_identifier(client: TestClient):
    login = client.post('/api/v1/auth/login', json={'identifier': 'admin@testco.com', 'password': 'admin12345'})
    assert login.status_code == 200
    assert 'access_token' in login.json()
