from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.item import Item
from app.models.organization import Organization
from app.models.warehouse import Warehouse


def _seed_baseline_entities(db_session: Session):
    org = db_session.execute(
        select(Organization).where(Organization.slug == 'testco')
    ).scalar_one()
    w1 = Warehouse(
        code='WH-A',
        name='Warehouse A',
        address='Address A',
        city='City',
        state='State',
        country='ET',
        latitude=8.98,
        longitude=38.76,
        capacity_units=1000,
        organization_id=org.id,
    )
    w2 = Warehouse(
        code='WH-B',
        name='Warehouse B',
        address='Address B',
        city='City',
        state='State',
        country='ET',
        latitude=8.99,
        longitude=38.77,
        capacity_units=1200,
        organization_id=org.id,
    )
    item = Item(
        sku='SKU-1',
        name='Test Item',
        category='General',
        unit_cost=10.0,
        reorder_level=30,
        organization_id=org.id,
    )
    db_session.add_all([w1, w2, item])
    db_session.flush()

    inventory = Inventory(
        warehouse_id=w1.id,
        item_id=item.id,
        quantity_on_hand=10,
        safety_stock=20,
        organization_id=org.id,
    )
    db_session.add(inventory)
    db_session.commit()


def test_shipment_lifecycle_and_delay_alert(client: TestClient, db_session: Session, operator_token: str):
    _seed_baseline_entities(db_session)
    headers = {'Authorization': f'Bearer {operator_token}'}

    create_resp = client.post(
        '/api/v1/shipments',
        json={
            'shipment_no': 'SHP-100',
            'origin_warehouse_code': 'WH-A',
            'destination_warehouse_code': 'WH-B',
            'sku': 'SKU-1',
            'quantity_units': 12,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    shipment_id = create_resp.json()['id']

    missing_reason = client.post(f'/api/v1/shipments/{shipment_id}/status', json={'status': 'delayed'}, headers=headers)
    assert missing_reason.status_code == 400

    delayed = client.post(
        f'/api/v1/shipments/{shipment_id}/status',
        json={'status': 'delayed', 'delay_reason': 'Port congestion'},
        headers=headers,
    )
    assert delayed.status_code == 200
    assert delayed.json()['status'] == 'delayed'

    alerts = client.get('/api/v1/alerts?status=open', headers=headers)
    assert alerts.status_code == 200
    assert any(row['alert_type'] == 'delayed_shipment' for row in alerts.json())


def test_alert_scan_and_acknowledge_flow(client: TestClient, db_session: Session, operator_token: str):
    _seed_baseline_entities(db_session)
    headers = {'Authorization': f'Bearer {operator_token}'}

    scan = client.post('/api/v1/alerts/scan', headers=headers)
    assert scan.status_code == 200
    assert any(row['alert_type'] == 'low_stock' for row in scan.json())

    alert_id = scan.json()[0]['id']
    ack = client.post(f'/api/v1/alerts/{alert_id}/acknowledge', json={'note': 'Investigating'}, headers=headers)
    assert ack.status_code == 200
    assert ack.json()['status'] == 'acknowledged'

    resolve = client.post(f'/api/v1/alerts/{alert_id}/resolve', json={'note': 'Replenished'}, headers=headers)
    assert resolve.status_code == 200
    assert resolve.json()['status'] == 'resolved'


def test_replenishment_generation_and_admin_approval(
    client: TestClient, db_session: Session, operator_token: str, admin_token: str, viewer_token: str
):
    _seed_baseline_entities(db_session)

    op_headers = {'Authorization': f'Bearer {operator_token}'}
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    viewer_headers = {'Authorization': f'Bearer {viewer_token}'}

    client.post(
        '/api/v1/orders',
        json={
            'order_date': str(date.today()),
            'warehouse_code': 'WH-A',
            'sku': 'SKU-1',
            'quantity': 40,
            'unit_price': 12.5,
            'customer_region': 'region-1',
        },
        headers=op_headers,
    )

    viewer_generate = client.post('/api/v1/planning/replenishment/generate', json={'horizon_weeks': 4}, headers=viewer_headers)
    assert viewer_generate.status_code == 403

    generated = client.post('/api/v1/planning/replenishment/generate', json={'horizon_weeks': 4}, headers=op_headers)
    assert generated.status_code == 200
    assert len(generated.json()) >= 1
    plan_id = generated.json()[0]['id']

    approved = client.post(f'/api/v1/planning/replenishment/{plan_id}/approve', json={}, headers=admin_headers)
    assert approved.status_code == 200
    assert approved.json()['status'] == 'approved'
