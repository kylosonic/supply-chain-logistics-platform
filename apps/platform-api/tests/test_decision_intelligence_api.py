from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def _create_cash_run(client: TestClient, token: str) -> dict:
    customer = client.post(
        '/api/v1/dispatch/customers',
        headers=_headers(token),
        json={
            'code': 'BRIEF-CUST',
            'name': 'Brief Retail Customer',
            'address': 'Bole, Addis Ababa',
            'latitude': 8.99,
            'longitude': 38.78,
        },
    )
    assert customer.status_code == 201, customer.text

    order = client.post(
        '/api/v1/dispatch/orders',
        headers=_headers(token),
        json={
            'order_no': 'BRIEF-ORDER-1',
            'customer_id': customer.json()['id'],
            'quantity_units': 12,
            'cod_amount_etb': '1500.00',
        },
    )
    assert order.status_code == 201, order.text

    driver = client.post(
        '/api/v1/drivers',
        headers=_headers(token),
        json={
            'full_name': 'Brief Driver',
            'phone': '+251933333333',
            'vehicle_plate': 'ET-3-90001',
        },
    )
    assert driver.status_code == 201, driver.text

    run = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token),
        json={
            'route_name': 'Brief cash run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [order.json()['id']],
            'driver_id': driver.json()['id'],
            'vehicle_capacity_units': 100,
            'max_stops': 10,
        },
    )
    assert run.status_code == 201, run.text
    return run.json()


def test_decision_brief_is_grounded_in_alerts_and_cash_records(
    client: TestClient, signup_workspace
):
    _org_id, token = signup_workspace('Brief Workspace')
    run = _create_cash_run(client, token)

    alert = client.post(
        '/api/v1/alerts',
        headers=_headers(token),
        json={
            'alert_type': 'manual',
            'severity': 'critical',
            'title': 'Customer has not confirmed receipt',
            'message': 'The dispatcher must call the customer before the next window.',
        },
    )
    assert alert.status_code == 201, alert.text

    triage = client.get('/api/v1/ops/exception-triage', headers=_headers(token))
    assert triage.status_code == 200, triage.text
    assert triage.json()[0]['alert_id'] == alert.json()['id']
    assert triage.json()[0]['suggested_action']
    assert triage.json()[0]['evidence'][0]['record_type'] == 'alert'

    cash = client.get('/api/v1/ops/cash-risk', headers=_headers(token))
    assert cash.status_code == 200, cash.text
    assert cash.json()[0]['driver_name'] == 'Brief Driver'
    assert cash.json()[0]['expected_etb'] == '1500.00'
    assert cash.json()[0]['shortfall_etb'] == '1500.00'
    assert 'cash shortfall' in cash.json()[0]['factors']

    brief = client.get('/api/v1/ops/decision-brief', headers=_headers(token))
    assert brief.status_code == 200, brief.text
    body = brief.json()
    assert body['generated_by'] == 'grounded_rules'
    assert body['triage'][0]['alert_id'] == alert.json()['id']
    assert body['cash_risk'][0]['driver_id'] is not None
    assert any(risk['kind'] == 'exceptions' for risk in body['risks'])
    assert any(risk['kind'] == 'cash_exposure' for risk in body['risks'])
    assert body['actions'][0]['href'] == '/alerts'
    assert len(run['stops']) == 1


def test_decision_brief_has_an_honest_empty_state(client: TestClient, signup_workspace):
    _org_id, token = signup_workspace('Empty Brief Workspace')

    brief = client.get('/api/v1/ops/decision-brief', headers=_headers(token))
    assert brief.status_code == 200, brief.text
    body = brief.json()
    assert body['risks'] == []
    assert body['actions'] == []
    assert body['cash_risk'] == []
    assert body['triage'] == []
    assert body['headline'] == '0 operating risk(s) need review. 0 recommended action(s) are available.'


def test_decision_brief_and_radar_are_tenant_scoped(
    client: TestClient, signup_workspace, orgless_token
):
    _org_a, token_a = signup_workspace('Brief Tenant A')
    _org_b, token_b = signup_workspace('Brief Tenant B')
    _create_cash_run(client, token_a)
    alert = client.post(
        '/api/v1/alerts',
        headers=_headers(token_a),
        json={
            'severity': 'high',
            'title': 'Tenant A private exception',
            'message': 'This must not appear in tenant B.',
        },
    )
    assert alert.status_code == 201, alert.text

    other_brief = client.get('/api/v1/ops/decision-brief', headers=_headers(token_b))
    assert other_brief.status_code == 200, other_brief.text
    assert other_brief.json()['cash_risk'] == []
    assert other_brief.json()['triage'] == []

    denied = client.get('/api/v1/ops/decision-brief', headers=_headers(orgless_token))
    assert denied.status_code == 403
