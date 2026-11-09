from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def test_complete_private_fleet_day(client, signup_workspace, db_session: Session):
    org_id, token = signup_workspace('Daily Operations Co')
    headers = _headers(token)

    customer_one = client.post(
        '/api/v1/dispatch/customers',
        headers=headers,
        json={
            'code': 'DAY-C1',
            'name': 'Morning Market',
            'phone': '+251955000001',
            'address': 'Kirkos, Addis Ababa',
            'latitude': 9.01,
            'longitude': 38.76,
        },
    )
    customer_two = client.post(
        '/api/v1/dispatch/customers',
        headers=headers,
        json={
            'code': 'DAY-C2',
            'name': 'Afternoon Shop',
            'phone': '+251955000002',
            'address': 'Yeka, Addis Ababa',
            'latitude': 9.04,
            'longitude': 38.81,
        },
    )
    assert customer_one.status_code == 201
    assert customer_two.status_code == 201

    order_one = client.post(
        '/api/v1/dispatch/orders',
        headers=headers,
        json={
            'order_no': 'DAY-1',
            'customer_id': customer_one.json()['id'],
            'quantity_units': 6,
            'cod_amount_etb': '600.00',
            'window_start': '2026-11-07T08:00:00+00:00',
            'window_end': '2026-11-07T11:00:00+00:00',
        },
    )
    order_two = client.post(
        '/api/v1/dispatch/orders',
        headers=headers,
        json={
            'order_no': 'DAY-2',
            'customer_id': customer_two.json()['id'],
            'quantity_units': 7,
            'cod_amount_etb': '700.00',
            'window_start': '2026-11-07T10:00:00+00:00',
            'window_end': '2026-11-07T14:00:00+00:00',
        },
    )
    assert order_one.status_code == 201
    assert order_two.status_code == 201

    driver_one = client.post(
        '/api/v1/drivers',
        headers=headers,
        json={'full_name': 'Driver One', 'phone': '+251955100001'},
    )
    driver_two = client.post(
        '/api/v1/drivers',
        headers=headers,
        json={'full_name': 'Driver Two', 'phone': '+251955100002'},
    )
    assert driver_one.status_code == 201
    assert driver_two.status_code == 201

    fleet = client.post(
        '/api/v1/dispatch/plan-fleet',
        headers=headers,
        json={
            'route_name': 'Friday distribution',
            'plan_date': '2026-11-07',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [order_one.json()['id'], order_two.json()['id']],
            'vehicles': [
                {
                    'driver_id': driver_one.json()['id'],
                    'vehicle_capacity_units': 10,
                },
                {
                    'driver_id': driver_two.json()['id'],
                    'vehicle_capacity_units': 10,
                },
            ],
        },
    )
    assert fleet.status_code == 201, fleet.text
    runs = fleet.json()['runs']
    assert len(runs) == 2
    assert fleet.json()['unassigned'] == []

    tracking_links: dict[str, str] = {}
    for run in runs:
        link = client.post(
            f"/api/v1/dispatch/runs/{run['id']}/driver-link",
            headers=headers,
        )
        assert link.status_code == 200, link.text
        driver_headers = {'X-Driver-Token': link.json()['token']}
        manifest = client.get(
            '/api/v1/dispatch/driver/manifest',
            headers=driver_headers,
        )
        assert manifest.status_code == 200, manifest.text
        for stop in manifest.json()['stops']:
            delivered = client.post(
                f"/api/v1/dispatch/driver/orders/{stop['order_id']}/status",
                headers=driver_headers,
                json={'status': 'delivered'},
            )
            assert delivered.status_code == 200, delivered.text
            declared = client.post(
                f"/api/v1/dispatch/driver/orders/{stop['order_id']}/cash",
                headers=driver_headers,
                json={'collected_etb': stop['cod_amount_etb']},
            )
            assert declared.status_code == 200, declared.text
            tracking = client.post(
                f"/api/v1/dispatch/orders/{stop['order_id']}/tracking-link",
                headers=headers,
            )
            assert tracking.status_code == 200, tracking.text
            tracking_links[stop['order_no']] = tracking.json()['token']

        close = client.post(
            f"/api/v1/dispatch/runs/{run['id']}/close-cash",
            headers=headers,
            json={
                'handed_over_etb': run['expected_cash_etb'],
                'deposit_bank': 'cbe',
                'deposit_reference': f"DAY-{run['id'][:8]}",
            },
        )
        assert close.status_code == 200, close.text
        assert close.json()['shortfall_etb'] == '0.00'

    customer_status = client.get(
        '/api/v1/dispatch/tracking',
        headers={'X-Tracking-Token': tracking_links['DAY-1']},
    )
    assert customer_status.status_code == 200, customer_status.text
    assert customer_status.json()['status'] == 'delivered'

    audits = db_session.execute(select(AuditEvent)).scalars().all()
    event_types = {event.event_type for event in audits}
    assert {
        'dispatch.fleet_planned',
        'dispatch.driver_status',
        'dispatch.cash_declared',
        'dispatch.cash_closed',
    } <= event_types
    assert all(str(event.organization_id) == org_id for event in audits)
