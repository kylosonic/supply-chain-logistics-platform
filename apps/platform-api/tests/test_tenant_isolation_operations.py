"""NB-64 — two-organization isolation regression suite (audit H-1).

Acceptance standard (`docs/behaviors/production-security-hardening.md` §4/§13):
two organizations with overlapping identifiers must never see or mutate each
other's operational data on any surface, and cross-tenant reads answer **404
Not Found** (never 403) so record existence is not leaked.

Surfaces covered here (the ones the audit flagged as global-role-only):

- ``GET/POST /shipments`` and ``POST /shipments/{id}/status``
- ``GET/POST /alerts``, ``/alerts/scan``, ``/alerts/{id}/acknowledge``
- ``GET /ops/audit-timeline``, ``/ops/exception-feed``, ``/ops/dock-appointments``,
  ``POST /ops/live-eta``
- ``GET /planning/replenishment``, ``POST /planning/replenishment/generate``,
  ``POST /planning/replenishment/{id}/approve``
- ``GET /routes/schedules``, ``/routes/schedules/{id}``, ``/routes/history``
- ``POST /forecast/weekly-demand``
- ``POST /ingestion/telematics``, ``/ingestion/iot-telemetry``

Org-less pass-through (legacy accounts) is pinned separately so the TECH-58
contract cannot silently regress.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.dock_appointment import DockAppointment
from app.models.replenishment import ReplenishmentPlan
from app.models.shipment import Shipment


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _create_shipment(client: TestClient, token: str, shipment_no: str) -> dict:
    """Seeded workspaces share warehouse codes WH-001..003 and SKU-001..003,
    so the same payload succeeds independently in both organizations."""
    resp = client.post(
        '/api/v1/shipments',
        headers=_headers(token),
        json={
            'shipment_no': shipment_no,
            'origin_warehouse_code': 'WH-001',
            'destination_warehouse_code': 'WH-002',
            'sku': 'SKU-001',
            'quantity_units': 25,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------


def test_shipments_are_invisible_across_orgs(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Ship Iso A')
    org_b, token_b = signup_workspace('Ship Iso B')

    a_shipment = _create_shipment(client, token_a, 'SHP-A-1')
    b_shipment = _create_shipment(client, token_b, 'SHP-B-1')

    list_a = client.get('/api/v1/shipments', headers=_headers(token_a))
    assert list_a.status_code == 200
    numbers_a = {row['shipment_no'] for row in list_a.json()}
    assert numbers_a == {'SHP-A-1'}

    list_b = client.get('/api/v1/shipments', headers=_headers(token_b))
    assert list_b.status_code == 200
    assert {row['shipment_no'] for row in list_b.json()} == {'SHP-B-1'}

    # Rows are stamped with their own org.
    rows = {
        row.shipment_no: row.organization_id
        for row in db_session.execute(select(Shipment)).scalars()
    }
    assert rows['SHP-A-1'] == UUID(org_a)
    assert rows['SHP-B-1'] == UUID(org_b)

    # Cross-tenant read is 404, not 403 (existence never leaked).
    cross = client.get(f"/api/v1/shipments/{b_shipment['id']}", headers=_headers(token_a))
    assert cross.status_code == 404
    assert cross.json()['detail'] == 'Shipment not found'

    own = client.get(f"/api/v1/shipments/{a_shipment['id']}", headers=_headers(token_a))
    assert own.status_code == 200


def test_cross_org_shipment_status_write_is_rejected(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Ship Write A')
    _, token_b = signup_workspace('Ship Write B')

    b_shipment = _create_shipment(client, token_b, 'SHP-B-2')

    resp = client.post(
        f"/api/v1/shipments/{b_shipment['id']}/status",
        headers=_headers(token_a),
        json={'status': 'delivered'},
    )
    assert resp.status_code == 404, resp.text

    # B's shipment is untouched.
    db_session.expire_all()
    row = db_session.execute(
        select(Shipment).where(Shipment.shipment_no == 'SHP-B-2')
    ).scalar_one()
    assert row.status == 'planned'


def test_shipment_duplicate_number_is_per_org(
    client: TestClient, signup_workspace, seed_csv_path
):
    """Both orgs may use the same shipment number without a false 409."""
    _, token_a = signup_workspace('Ship Dup A')
    _, token_b = signup_workspace('Ship Dup B')

    _create_shipment(client, token_a, 'SHP-SHARED')

    duplicate_same_org = client.post(
        '/api/v1/shipments',
        headers=_headers(token_a),
        json={
            'shipment_no': 'SHP-SHARED',
            'origin_warehouse_code': 'WH-001',
            'destination_warehouse_code': 'WH-002',
            'sku': 'SKU-001',
            'quantity_units': 5,
        },
    )
    assert duplicate_same_org.status_code == 409

    _create_shipment(client, token_b, 'SHP-SHARED')


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


def test_alerts_are_invisible_and_unmutable_across_orgs(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Alert Iso A')
    org_b, token_b = signup_workspace('Alert Iso B')

    created_b = client.post(
        '/api/v1/alerts',
        headers=_headers(token_b),
        json={
            'alert_type': 'low_stock',
            'severity': 'high',
            'title': 'B-only alert',
            'message': 'belongs to org B',
        },
    )
    assert created_b.status_code == 201, created_b.text
    alert_b = created_b.json()

    list_a = client.get('/api/v1/alerts', headers=_headers(token_a))
    assert list_a.status_code == 200
    assert list_a.json() == []

    list_b = client.get('/api/v1/alerts', headers=_headers(token_b))
    assert {row['title'] for row in list_b.json()} == {'B-only alert'}

    row = db_session.execute(
        select(Alert).where(Alert.title == 'B-only alert')
    ).scalar_one()
    assert row.organization_id == UUID(org_b)

    # A cannot acknowledge, resolve, or auto-resolve B's alert.
    for suffix in ('acknowledge', 'resolve', 'auto-resolve'):
        resp = client.post(
            f"/api/v1/alerts/{alert_b['id']}/{suffix}",
            headers=_headers(token_a),
            json={'note': 'hijack'},
        )
        assert resp.status_code == 404, f'{suffix}: {resp.status_code} {resp.text}'


def test_alert_scan_only_covers_callers_org(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    """A scan in org A must not generate alerts from org B's inventory."""
    org_a, token_a = signup_workspace('Scan A')
    org_b, token_b = signup_workspace('Scan B')

    # Drive B's inventory below safety stock, leave A's intact.
    from app.models.inventory import Inventory

    b_inventory = db_session.execute(
        select(Inventory).where(Inventory.organization_id == UUID(org_b))
    ).scalars().all()
    assert b_inventory, 'expected seeded inventory for org B'
    for row in b_inventory:
        row.quantity_on_hand = 0
    db_session.commit()

    scan_a = client.post('/api/v1/alerts/scan', headers=_headers(token_a))
    assert scan_a.status_code == 200, scan_a.text
    assert scan_a.json() == [], 'org A scan picked up org B inventory'

    scan_b = client.post('/api/v1/alerts/scan', headers=_headers(token_b))
    assert scan_b.status_code == 200, scan_b.text
    assert scan_b.json(), 'org B should have generated its own low-stock alerts'

    # Every generated alert belongs to B.
    orgs = {
        row.organization_id
        for row in db_session.execute(
            select(Alert).where(Alert.alert_type == 'low_stock')
        ).scalars()
    }
    assert orgs == {UUID(org_b)}


# ---------------------------------------------------------------------------
# Ops surfaces
# ---------------------------------------------------------------------------


def test_audit_timeline_and_exception_feed_are_org_scoped(
    client: TestClient, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Ops Iso A')
    _, token_b = signup_workspace('Ops Iso B')

    # B performs an auditable action and raises an exception (delayed shipment).
    b_shipment = _create_shipment(client, token_b, 'SHP-OPS-B')
    delayed = client.post(
        f"/api/v1/shipments/{b_shipment['id']}/status",
        headers=_headers(token_b),
        json={'status': 'delayed', 'delay_reason': 'road closure'},
    )
    assert delayed.status_code == 200, delayed.text

    timeline_a = client.get('/api/v1/ops/audit-timeline', headers=_headers(token_a))
    assert timeline_a.status_code == 200
    descriptions_a = ' '.join(row['description'] for row in timeline_a.json())
    assert 'SHP-OPS-B' not in descriptions_a

    timeline_b = client.get('/api/v1/ops/audit-timeline', headers=_headers(token_b))
    assert 'SHP-OPS-B' in ' '.join(row['description'] for row in timeline_b.json())

    feed_a = client.get('/api/v1/ops/exception-feed', headers=_headers(token_a))
    assert feed_a.status_code == 200
    body_a = feed_a.json()
    assert body_a['summary']['delayed_shipments'] == 0
    assert all('SHP-OPS-B' not in item['title'] for item in body_a['items'])

    feed_b = client.get('/api/v1/ops/exception-feed', headers=_headers(token_b))
    assert feed_b.json()['summary']['delayed_shipments'] == 1


def test_dock_appointments_and_live_eta_are_org_scoped(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Dock A')
    org_b, token_b = signup_workspace('Dock B')

    from app.models.warehouse import Warehouse

    b_warehouse = db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == UUID(org_b))
    ).scalars().first()
    a_warehouse = db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == UUID(org_a))
    ).scalars().first()
    assert b_warehouse is not None and a_warehouse is not None

    when = datetime.now(UTC) + timedelta(hours=2)

    # A writing against B's warehouse is refused.
    cross = client.post(
        '/api/v1/ops/live-eta',
        headers=_headers(token_a),
        json={
            'warehouse_id': str(b_warehouse.id),
            'truck_id': 'TRUCK-X',
            'expected_time': when.isoformat(),
        },
    )
    assert cross.status_code == 404, cross.text

    # A against its own warehouse succeeds and stays invisible to B.
    own = client.post(
        '/api/v1/ops/live-eta',
        headers=_headers(token_a),
        json={
            'warehouse_id': str(a_warehouse.id),
            'truck_id': 'TRUCK-A',
            'expected_time': when.isoformat(),
        },
    )
    assert own.status_code == 200, own.text

    list_b = client.get('/api/v1/ops/dock-appointments', headers=_headers(token_b))
    assert list_b.status_code == 200
    assert list_b.json() == []

    list_a = client.get('/api/v1/ops/dock-appointments', headers=_headers(token_a))
    assert [row['truck_id'] for row in list_a.json()] == ['TRUCK-A']

    appointment = db_session.execute(select(DockAppointment)).scalar_one()
    assert appointment.organization_id == UUID(org_a)


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def test_replenishment_plans_are_org_scoped(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Plan A')
    org_b, token_b = signup_workspace('Plan B')

    generated_b = client.post(
        '/api/v1/planning/replenishment/generate',
        headers=_headers(token_b),
        json={'horizon_weeks': 4},
    )
    assert generated_b.status_code == 200, generated_b.text
    assert generated_b.json(), 'expected org B to generate plans'
    # B is the workspace owner (org admin) so approval is allowed.
    plan_b_id = generated_b.json()[0]['id']

    list_a = client.get('/api/v1/planning/replenishment', headers=_headers(token_a))
    assert list_a.status_code == 200
    assert list_a.json() == []

    list_b = client.get('/api/v1/planning/replenishment', headers=_headers(token_b))
    assert len(list_b.json()) == len(generated_b.json())

    orgs = {
        row.organization_id
        for row in db_session.execute(select(ReplenishmentPlan)).scalars()
    }
    assert orgs == {UUID(org_b)}

    cross_approve = client.post(
        f'/api/v1/planning/replenishment/{plan_b_id}/approve',
        headers=_headers(token_a),
        json={'approved_quantity': 10},
    )
    assert cross_approve.status_code == 404, cross_approve.text

    cross_reject = client.post(
        f'/api/v1/planning/replenishment/{plan_b_id}/reject',
        headers=_headers(token_a),
        json={'reason': 'not mine'},
    )
    assert cross_reject.status_code == 404, cross_reject.text


# ---------------------------------------------------------------------------
# Routes and forecast
# ---------------------------------------------------------------------------


def test_route_history_and_schedules_are_org_scoped(
    client: TestClient, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Route Iso A')
    _, token_b = signup_workspace('Route Iso B')

    payload = {
        'route_name': 'B-Only Route',
        'schedule_date': str(datetime.now(UTC).date()),
        'start_warehouse_code': 'WH-001',
        'vehicle_capacity_units': 500,
        'max_stops': 3,
        'persist_schedule': True,
        'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
    }
    run_b = client.post('/api/v1/routes/optimize', headers=_headers(token_b), json=payload)
    assert run_b.status_code == 200, run_b.text

    history_a = client.get('/api/v1/routes/history', headers=_headers(token_a))
    assert history_a.status_code == 200
    assert history_a.json() == []

    history_b = client.get('/api/v1/routes/history', headers=_headers(token_b))
    assert [row['route_name'] for row in history_b.json()] == ['B-Only Route']

    schedules_a = client.get('/api/v1/routes/schedules', headers=_headers(token_a))
    assert schedules_a.status_code == 200
    assert schedules_a.json() == []

    schedules_b = client.get('/api/v1/routes/schedules', headers=_headers(token_b))
    assert [row['route_name'] for row in schedules_b.json()] == ['B-Only Route']
    schedule_b_id = schedules_b.json()[0]['id']

    cross = client.get(
        f'/api/v1/routes/schedules/{schedule_b_id}', headers=_headers(token_a)
    )
    assert cross.status_code == 404
    assert cross.json()['detail'] == 'Route schedule not found'


def test_forecast_rejects_org_without_orders(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    """A forecast must not silently answer from another tenant's order history."""
    org_a, token_a = signup_workspace('Forecast A')
    _, token_b = signup_workspace('Forecast B')

    from app.models.order import HistoricalOrder

    # Remove org A's order history, leave B's intact.
    for row in db_session.execute(
        select(HistoricalOrder).where(HistoricalOrder.organization_id == UUID(org_a))
    ).scalars():
        db_session.delete(row)
    db_session.commit()

    resp_a = client.post(
        '/api/v1/forecast/weekly-demand', headers=_headers(token_a), json={'horizon_weeks': 1}
    )
    assert resp_a.status_code == 400, resp_a.text
    assert resp_a.json()['detail'] == 'No historical orders found'

    resp_b = client.post(
        '/api/v1/forecast/weekly-demand', headers=_headers(token_b), json={'horizon_weeks': 1}
    )
    assert resp_b.status_code == 200, resp_b.text


# ---------------------------------------------------------------------------
# Telemetry ingestion (cross-tenant writes)
# ---------------------------------------------------------------------------


def test_telematics_and_iot_writes_cannot_cross_tenants(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    """Telemetry ingestion is a *write* path, so it must be strictly scoped.

    Seeded workspaces deliberately share natural codes (``TRUCK-1001``,
    ``SKU-001``) across organizations, so this test gives org B a
    tenant-unique vehicle code: org A must then be unable to reach it at all.
    """
    org_a, token_a = signup_workspace('Telemetry A')
    org_b, token_b = signup_workspace('Telemetry B')

    from app.models.fleet_asset import FleetAsset

    b_only = FleetAsset(
        organization_id=UUID(org_b),
        vehicle_code='TRUCK-B-ONLY',
        driver_name='B Driver',
        capacity_units=100,
        status='IDLE',
        data_origin='real',
    )
    db_session.add(b_only)
    db_session.commit()
    db_session.refresh(b_only)
    original_lat, original_lon = b_only.latitude, b_only.longitude

    payload = {
        'asset_id': 'TRUCK-B-ONLY',
        'latitude': 1.0,
        'longitude': 2.0,
        'speed_mph': 30,
        'heading_degrees': 90,
        'timestamp': datetime.now(UTC).isoformat(),
    }

    cross = client.post('/api/v1/ingestion/telematics', headers=_headers(token_a), json=payload)
    assert cross.status_code == 404, cross.text

    # B's asset GPS is untouched by A's attempt.
    db_session.expire_all()
    unchanged = db_session.get(FleetAsset, b_only.id)
    assert (unchanged.latitude, unchanged.longitude) == (original_lat, original_lon)
    assert unchanged.last_telemetry_at is None

    # B may write to its own asset.
    own = client.post('/api/v1/ingestion/telematics', headers=_headers(token_b), json=payload)
    assert own.status_code == 200, own.text

    db_session.expire_all()
    updated = db_session.get(FleetAsset, b_only.id)
    assert (updated.latitude, updated.longitude) == (1.0, 2.0)
    assert updated.last_telemetry_at is not None

    # IoT telemetry for another tenant's SKU is refused (404, not a silent
    # no-op) and raises no alert in either tenant.
    iot = {
        'sku': 'SKU-001',
        'latitude': 9.0,
        'longitude': 38.8,
        'temperature_c': 99.0,
        'timestamp': datetime.now(UTC).isoformat(),
    }

    # Give org B a tenant-unique SKU with a temperature threshold.
    from app.models.item import Item

    b_item = Item(
        organization_id=UUID(org_b),
        sku='SKU-B-ONLY',
        name='Cold chain B item',
        category='Perishable',
        unit_cost=5.0,
        reorder_level=1,
        temperature_threshold=8.0,
        data_origin='real',
    )
    db_session.add(b_item)
    db_session.commit()

    cross_iot = client.post(
        '/api/v1/ingestion/iot-telemetry',
        headers=_headers(token_a),
        json={**iot, 'sku': 'SKU-B-ONLY'},
    )
    assert cross_iot.status_code == 404, cross_iot.text

    org_b_alerts = db_session.execute(
        select(Alert).where(
            Alert.alert_type == 'temperature_excursion',
            Alert.organization_id == UUID(org_b),
        )
    ).scalars().all()
    assert org_b_alerts == [], 'org A telemetry injected an alert into org B'

    # B's own excursion raises exactly one alert stamped with B.
    own_iot = client.post(
        '/api/v1/ingestion/iot-telemetry',
        headers=_headers(token_b),
        json={**iot, 'sku': 'SKU-B-ONLY'},
    )
    assert own_iot.status_code == 200, own_iot.text
    assert own_iot.json()['alert_triggered'] is True

    db_session.expire_all()
    org_b_alerts = db_session.execute(
        select(Alert).where(
            Alert.alert_type == 'temperature_excursion',
            Alert.organization_id == UUID(org_b),
        )
    ).scalars().all()
    org_a_alerts = db_session.execute(
        select(Alert).where(
            Alert.alert_type == 'temperature_excursion',
            Alert.organization_id == UUID(org_a),
        )
    ).scalars().all()
    assert org_a_alerts == [], 'org A raised an excursion alert for a foreign SKU'


# ---------------------------------------------------------------------------
# Legacy pass-through (TECH-58 contract must not regress)
# ---------------------------------------------------------------------------


def test_orgless_actor_keeps_unfiltered_pass_through(
    client: TestClient, db_session: Session):
    """An account with no organization still sees the global dataset.

    This is the pinned pre-NB-64 contract for legacy/seeded demo accounts
    (`warehouses.py` TECH-58 behaviour). It must survive the tenant-scoping
    work, otherwise single-tenant deployments break.

    Note: registration requires an authenticated admin once any user exists
    (NB-68 closed the "first visitor becomes admin" bootstrap door), so the
    legacy actor is created by the seeded admin.
    """
    from app.schemas.auth import UserRole
    from app.services.security import create_access_token

    admin_token = client.post(
        '/api/v1/auth/login', json={'username': 'admin', 'password': 'admin12345'}
    ).json()['access_token']

    resp = client.post(
        '/api/v1/auth/register',
        headers=_headers(admin_token),
        json={
            'username': 'legacyops',
            'email': 'legacyops@example.com',
            'full_name': 'Legacy Ops',
            'password': 'VeryStrongPass9',
            'role': 'operator',
        },
    )
    assert resp.status_code == 201, resp.text
    legacy_id = resp.json()['id']

    from app.models.user import User

    user = db_session.get(User, legacy_id)
    assert user.role == UserRole.OPERATOR
    token = create_access_token(subject=str(user.id), role=UserRole.OPERATOR)

    # No membership row exists, so the actor is org-less: unfiltered listing.
    shipments = client.get('/api/v1/shipments', headers=_headers(token))
    assert shipments.status_code == 200

    alerts = client.get('/api/v1/alerts', headers=_headers(token))
    assert alerts.status_code == 200

    # Authorization still applies: a viewer-role token cannot write.
    viewer_token = client.post(
        '/api/v1/auth/login', json={'username': 'viewer', 'password': 'viewer12345'}
    ).json()['access_token']
    denied = client.post(
        '/api/v1/alerts',
        headers=_headers(viewer_token),
        json={
            'alert_type': 'low_stock',
            'severity': 'high',
            'title': 'viewer cannot create',
            'message': 'nope',
        },
    )
    assert denied.status_code == 403
