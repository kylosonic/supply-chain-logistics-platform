from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usage_meter import OrganizationUsageCounter
from app.models.warehouse import Warehouse


def _seed_warehouses(db_session: Session) -> None:
    db_session.add_all(
        [
            Warehouse(
                code='WH-A',
                name='Warehouse A',
                address='Address A',
                city='City',
                state='State',
                country='ET',
                latitude=8.98,
                longitude=38.76,
                capacity_units=1000,
            ),
            Warehouse(
                code='WH-B',
                name='Warehouse B',
                address='Address B',
                city='City',
                state='State',
                country='ET',
                latitude=8.99,
                longitude=38.77,
                capacity_units=1200,
            ),
            Warehouse(
                code='WH-C',
                name='Warehouse C',
                address='Address C',
                city='City',
                state='State',
                country='ET',
                latitude=9.01,
                longitude=38.79,
                capacity_units=900,
            ),
        ]
    )
    db_session.commit()


def _company_signup_token(client: TestClient, suffix: str) -> str:
    resp = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': f'Route Meter {suffix}',
            'company_email': f'owner-{suffix}@routemeter.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': 'starter',
        },
    )
    assert resp.status_code == 201
    token = resp.json()['access_token']
    # Signup always creates a Free org; upgrade into Starter (7-day trial,
    # full write access) before optimizing.
    selected = client.post(
        '/api/v1/subscriptions/select-tier',
        headers={'Authorization': f'Bearer {token}'},
        json={'tier': 'starter'},
    )
    assert selected.status_code == 200
    return token


def _optimize_payload(deliveries: list[dict[str, int | str]]) -> dict:
    return {
        'route_name': 'Daily Dispatch',
        'schedule_date': str(date.today()),
        'start_warehouse_code': 'WH-A',
        'deliveries': deliveries,
        'vehicle_capacity_units': 250,
        'max_stops': 10,
        'speed_kmh': 45,
        'cost_per_km': 1.5,
        'persist_schedule': False,
    }


def test_route_optimization_automatically_records_usage(client: TestClient, db_session: Session):
    _seed_warehouses(db_session)
    token = _company_signup_token(client, suffix='auto')
    headers = {'Authorization': f'Bearer {token}'}

    first_payload = _optimize_payload(
        [
            {'warehouse_code': 'WH-B', 'demand_units': 40},
            {'warehouse_code': 'WH-C', 'demand_units': 35},
        ]
    )
    first = client.post('/api/v1/routes/optimize', json=first_payload, headers=headers)
    assert first.status_code == 200

    second_payload = _optimize_payload([{'warehouse_code': 'WH-B', 'demand_units': 20}])
    second = client.post('/api/v1/routes/optimize', json=second_payload, headers=headers)
    assert second.status_code == 200

    usage = client.get('/api/v1/subscriptions/usage/me', headers=headers)
    assert usage.status_code == 200
    body = usage.json()
    assert body['metric'] == 'delivery_tasks'
    assert body['used_units'] == 3
    assert body['included_units'] == 2500
    assert body['overage_units'] == 0


def test_route_optimization_without_membership_does_not_fail(client: TestClient, db_session: Session, operator_token: str):
    _seed_warehouses(db_session)
    headers = {'Authorization': f'Bearer {operator_token}'}

    payload = _optimize_payload([{'warehouse_code': 'WH-B', 'demand_units': 25}])
    resp = client.post('/api/v1/routes/optimize', json=payload, headers=headers)
    assert resp.status_code == 200

    counters = db_session.execute(select(OrganizationUsageCounter)).scalars().all()
    assert counters == []