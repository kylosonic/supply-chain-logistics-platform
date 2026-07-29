from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.item import Item
from app.models.warehouse import Warehouse


def _seed_route_and_inventory_entities(db_session: Session) -> None:
    warehouses = [
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
    item = Item(sku='SKU-1', name='Test Item', category='General', unit_cost=10.0, reorder_level=30)

    db_session.add_all([*warehouses, item])
    db_session.flush()
    db_session.add(
        Inventory(
            warehouse_id=warehouses[0].id,
            item_id=item.id,
            quantity_on_hand=10,
            safety_stock=20,
        )
    )
    db_session.commit()


def _company_signup_token(client: TestClient, suffix: str) -> str:
    response = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': f'Insight Co {suffix}',
            'company_email': f'owner-{suffix}@insightco.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': 'starter',
        },
    )
    assert response.status_code == 201
    return response.json()['access_token']


def test_route_history_and_audit_timeline_are_recorded(client: TestClient, db_session: Session):
    _seed_route_and_inventory_entities(db_session)
    token = _company_signup_token(client, 'history')
    headers = {'Authorization': f'Bearer {token}'}

    optimize = client.post(
        '/api/v1/routes/optimize',
        json={
            'route_name': 'Morning Dispatch',
            'schedule_date': str(date.today()),
            'start_warehouse_code': 'WH-A',
            'deliveries': [
                {'warehouse_code': 'WH-B', 'demand_units': 25},
                {'warehouse_code': 'WH-C', 'demand_units': 20},
            ],
            'vehicle_capacity_units': 120,
            'max_stops': 10,
            'speed_kmh': 45,
            'cost_per_km': 1.5,
            'persist_schedule': False,
        },
        headers=headers,
    )
    assert optimize.status_code == 200

    history = client.get('/api/v1/routes/history', headers=headers)
    assert history.status_code == 200
    history_body = history.json()
    assert len(history_body) >= 1
    run_id = history_body[0]['id']
    assert history_body[0]['route_name'] == 'Morning Dispatch'

    detail = client.get(f'/api/v1/routes/history/{run_id}', headers=headers)
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body['deliveries_count'] == 2
    assert len(detail_body['deliveries']) == 2

    audit = client.get('/api/v1/ops/audit-timeline', headers=headers)
    assert audit.status_code == 200
    assert any(event['event_type'] == 'route.optimized' for event in audit.json())


def test_exception_feed_combines_alerts_plans_and_route_run_exceptions(client: TestClient, db_session: Session):
    _seed_route_and_inventory_entities(db_session)
    token = _company_signup_token(client, 'feed')
    headers = {'Authorization': f'Bearer {token}'}

    manual_alert = client.post(
        '/api/v1/alerts',
        json={
            'title': 'Manual coordination issue',
            'message': 'Driver handoff requires supervisor review.',
            'severity': 'high',
        },
        headers=headers,
    )
    assert manual_alert.status_code == 201

    order = client.post(
        '/api/v1/orders',
        json={
            'order_date': str(date.today()),
            'warehouse_code': 'WH-A',
            'sku': 'SKU-1',
            'quantity': 40,
            'unit_price': 12.5,
            'customer_region': 'region-1',
        },
        headers=headers,
    )
    assert order.status_code == 201

    generated = client.post('/api/v1/planning/replenishment/generate', json={'horizon_weeks': 4}, headers=headers)
    assert generated.status_code == 200
    assert len(generated.json()) >= 1

    optimize = client.post(
        '/api/v1/routes/optimize',
        json={
            'route_name': 'Capacity Stress Test',
            'schedule_date': str(date.today()),
            'start_warehouse_code': 'WH-A',
            'deliveries': [
                {'warehouse_code': 'WH-B', 'demand_units': 25},
                {'warehouse_code': 'WH-C', 'demand_units': 25},
            ],
            'vehicle_capacity_units': 30,
            'max_stops': 10,
            'speed_kmh': 45,
            'cost_per_km': 1.5,
            'persist_schedule': False,
        },
        headers=headers,
    )
    assert optimize.status_code == 200
    assert len(optimize.json()['unassigned_deliveries']) >= 1

    feed = client.get('/api/v1/ops/exception-feed', headers=headers)
    assert feed.status_code == 200
    payload = feed.json()
    sources = {item['source_type'] for item in payload['items']}

    assert {'alert', 'replenishment_plan', 'route_optimization_run'}.issubset(sources)
    assert payload['summary']['open_alerts'] >= 1
    assert payload['summary']['pending_replenishment_plans'] >= 1
    assert payload['summary']['route_runs_with_unassigned_deliveries'] >= 1