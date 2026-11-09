from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.dispatch import DeliveryOrder, DispatchRun


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def _customer(client, token: str, code: str):
    response = client.post(
        '/api/v1/dispatch/customers',
        headers=_headers(token),
        json={
            'code': code,
            'name': f'Customer {code}',
            'address': 'Addis Ababa',
            'latitude': 9.0,
            'longitude': 38.75,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _order(client, token: str, order_no: str, customer_id: str, quantity: int):
    response = client.post(
        '/api/v1/dispatch/orders',
        headers=_headers(token),
        json={
            'order_no': order_no,
            'customer_id': customer_id,
            'quantity_units': quantity,
            'cod_amount_etb': str(quantity * 100),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _driver(client, token: str, name: str, phone: str):
    response = client.post(
        '/api/v1/drivers',
        headers=_headers(token),
        json={'full_name': name, 'phone': phone},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _fleet_payload(order_ids: list[str], vehicles: list[dict], name: str = 'Fleet plan'):
    return {
        'route_name': name,
        'plan_date': '2026-11-07',
        'start_label': 'Main depot',
        'start_latitude': 9.0,
        'start_longitude': 38.75,
        'order_ids': order_ids,
        'vehicles': vehicles,
    }


def test_fleet_plan_splits_orders_across_drivers(
    client,
    signup_workspace,
    db_session: Session,
):
    org_id, token = signup_workspace('Fleet Planning Co')
    customer_one = _customer(client, token, 'FLEET-C1')
    customer_two = _customer(client, token, 'FLEET-C2')
    first_order = _order(client, token, 'FLT-1', customer_one['id'], 6)
    second_order = _order(client, token, 'FLT-2', customer_two['id'], 7)
    first_driver = _driver(client, token, 'First Driver', '+251944000001')
    second_driver = _driver(client, token, 'Second Driver', '+251944000002')

    response = client.post(
        '/api/v1/dispatch/plan-fleet',
        headers=_headers(token),
        json=_fleet_payload(
            [first_order['id'], second_order['id']],
            [
                {'driver_id': first_driver['id'], 'vehicle_capacity_units': 10},
                {'driver_id': second_driver['id'], 'vehicle_capacity_units': 10},
            ],
        ),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body['unassigned'] == []
    assert len(body['runs']) == 2
    assert {run['driver_id'] for run in body['runs']} == {
        first_driver['id'],
        second_driver['id'],
    }
    assert sum(len(run['stops']) for run in body['runs']) == 2
    assert all(run['route_name'].startswith('Fleet plan - ') for run in body['runs'])

    db_session.expire_all()
    orders = db_session.execute(select(DeliveryOrder)).scalars().all()
    assert len({str(order.dispatch_run_id) for order in orders}) == 2
    assert all(order.status == 'assigned' for order in orders)
    runs = db_session.execute(select(DispatchRun)).scalars().all()
    assert len(runs) == 2
    assert all(str(run.organization_id) == org_id for run in runs)

    audit = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'dispatch.fleet_planned')
    ).scalar_one()
    assert str(audit.organization_id) == org_id
    assert audit.payload['vehicle_count'] == 2


def test_fleet_plan_reports_orders_that_cannot_fit(client, signup_workspace):
    _org_id, token = signup_workspace('Fleet Capacity Co')
    customer = _customer(client, token, 'FLEET-CAP')
    small = _order(client, token, 'FLT-5', customer['id'], 5)
    oversized = _order(client, token, 'FLT-20', customer['id'], 20)
    driver = _driver(client, token, 'Capacity Driver', '+251944000003')

    response = client.post(
        '/api/v1/dispatch/plan-fleet',
        headers=_headers(token),
        json=_fleet_payload(
            [small['id'], oversized['id']],
            [{'driver_id': driver['id'], 'vehicle_capacity_units': 10}],
        ),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body['runs']) == 1
    assert [stop['order_id'] for stop in body['runs'][0]['stops']] == [small['id']]
    assert body['unassigned'] == [
        {
            'order_id': oversized['id'],
            'order_no': 'FLT-20',
            'reason': 'exceeds_vehicle_capacity',
        }
    ]


def test_fleet_plan_rejects_duplicate_driver_vehicles(client, signup_workspace):
    _org_id, token = signup_workspace('Fleet Duplicate Co')
    customer = _customer(client, token, 'FLEET-DUP')
    order = _order(client, token, 'FLT-DUP-1', customer['id'], 5)
    driver = _driver(client, token, 'Duplicate Driver', '+251944000004')

    response = client.post(
        '/api/v1/dispatch/plan-fleet',
        headers=_headers(token),
        json=_fleet_payload(
            [order['id']],
            [
                {'driver_id': driver['id'], 'vehicle_capacity_units': 10},
                {'driver_id': driver['id'], 'vehicle_capacity_units': 10},
            ],
        ),
    )
    assert response.status_code == 422
    assert 'different driver' in response.json()['detail']
    assert client.get('/api/v1/dispatch/runs', headers=_headers(token)).json() == []
