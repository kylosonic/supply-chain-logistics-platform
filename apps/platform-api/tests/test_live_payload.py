from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.endpoints.live import _dispatch_overview
from app.models.dispatch import Customer, DeliveryOrder, DispatchRun
from app.models.driver import Driver
from app.models.organization import Organization
from app.services.live_feed import build_live_snapshot


def test_build_live_snapshot_shape():
    payload = build_live_snapshot(
        inventory_rows=[
            {
                'warehouse_code': 'WH-001',
                'warehouse_name': 'Main',
                'total_quantity_on_hand': 500,
                'total_safety_stock': 120,
                'utilization_percent': 45.5,
            }
        ],
        route_rows=[
            {
                'id': 'r1',
                'route_name': 'Route A',
                'schedule_date': '2026-05-18',
                'total_distance_km': 100.0,
                'total_cost': 150.0,
                'estimated_duration_min': 180,
                'status': 'planned',
            }
        ],
        forecast_rows=[
            {
                'week_start': '2026-05-18',
                'warehouse_code': 'WH-001',
                'sku': 'SKU-001',
                'predicted_demand': 82.0,
            }
        ],
        dispatch_overview={
            'updated_at': '2026-05-18T10:00:00+00:00',
            'runs': [
                {
                    'id': 'run-1',
                    'route_name': 'Morning delivery',
                    'status': 'planned',
                    'terminal_stops': 0,
                    'total_stops': 3,
                }
            ],
        },
    )

    assert payload['type'] == 'live_update'
    assert 'server_time' in payload
    assert len(payload['inventory_overview']) == 1
    assert len(payload['route_summaries']) == 1
    assert len(payload['forecast_preview']) == 1
    assert payload['dispatch_overview']['runs'][0]['route_name'] == 'Morning delivery'


def test_dispatch_overview_is_tenant_scoped_and_reports_progress(db_session: Session):
    org = db_session.execute(
        select(Organization).where(Organization.slug == 'testco')
    ).scalar_one()
    customer = Customer(
        organization_id=org.id,
        code='LIVE-CUST-1',
        name='Live Customer',
        address='Bole, Addis Ababa',
        latitude=9.0,
        longitude=38.75,
    )
    driver = Driver(
        organization_id=org.id,
        full_name='Live Driver',
        phone='+251933333333',
    )
    db_session.add_all([customer, driver])
    db_session.flush()

    run = DispatchRun(
        organization_id=org.id,
        route_name='Live morning run',
        plan_date=date(2026, 11, 7),
        start_label='Main depot',
        start_latitude=9.0,
        start_longitude=38.75,
        vehicle_capacity_units=50,
        max_stops=10,
        expected_cash_etb=Decimal('250.00'),
        status='planned',
        driver_id=driver.id,
    )
    db_session.add(run)
    db_session.flush()

    order = DeliveryOrder(
        organization_id=org.id,
        customer_id=customer.id,
        dispatch_run_id=run.id,
        driver_id=driver.id,
        order_no='LIVE-DO-1',
        quantity_units=5,
        cod_amount_etb=Decimal('250.00'),
        status='delivered',
        collected_cash_etb=Decimal('200.00'),
    )
    db_session.add(order)
    db_session.commit()

    overview = _dispatch_overview(db_session, org.id)
    assert overview['updated_at'] is not None
    assert len(overview['runs']) == 1
    summary = overview['runs'][0]
    assert summary['route_name'] == 'Live morning run'
    assert summary['driver_name'] == 'Live Driver'
    assert summary['total_stops'] == 1
    assert summary['terminal_stops'] == 1
    assert summary['progress_percent'] == 100.0
    assert summary['expected_cash_etb'] == '250.00'
    assert summary['collected_cash_etb'] == '200.00'

    other_org = Organization(
        name='Other Co',
        slug='other-live-co',
        primary_email_domain='other-live.example',
    )
    db_session.add(other_org)
    db_session.commit()
    assert _dispatch_overview(db_session, other_org.id) == {
        'updated_at': None,
        'runs': [],
    }
