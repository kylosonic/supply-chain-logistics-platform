"""Phase 4 seeding tests (blueprint §10.2 — test_activation_seeding.py, NB-25).

Covers per-workspace sample seeding at signup, origin/org scoping, the
seed audit event, idempotency + two-org isolation (§0A composite-unique
proof), operational usability of seeded data, supersede semantics
(decision #3) and org-scoped uploads (decision #13).
"""

from uuid import UUID

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.warehouse import Warehouse
from tests.conftest import (
    real_inventory_csv,
    real_items_csv,
    real_warehouse_csv,
)


def _optimize_payload() -> dict:
    return {
        'route_name': 'Seed Smoke Route',
        'schedule_date': '2026-08-10',
        'start_warehouse_code': 'WH-001',
        'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 10}],
        'vehicle_capacity_units': 100,
        'max_stops': 5,
        'speed_kmh': 45,
        'cost_per_km': 1.5,
        'persist_schedule': False,
        'minimize_carbon_footprint': False,
    }


def _seed_counts(session: Session, org_id: str) -> dict[str, int]:
    org_uuid = UUID(org_id)
    return {
        category: session.execute(
            select(func.count())
            .select_from(model)
            .where(model.organization_id == org_uuid, model.data_origin == 'sample')
        ).scalar_one()
        for category, model in (
            ('warehouses', Warehouse),
            ('items', Item),
            ('fleet_assets', FleetAsset),
            ('inventory', Inventory),
            ('orders', HistoricalOrder),
        )
    }


def test_signup_seeds_all_five_categories_per_workspace(
    client, db_session: Session, signup_workspace, seed_csv_path, sample_row_counts
):
    org_id, _ = signup_workspace()
    counts = sample_row_counts(org_id)

    assert counts['warehouses'] > 0
    assert counts['items'] > 0
    assert counts['fleet_assets'] > 0
    assert counts['inventory'] > 0
    assert counts['orders'] > 0

    # counts must match the shipped CSVs exactly
    for category in ('warehouses', 'items', 'fleet_assets', 'inventory', 'orders'):
        df = pd.read_csv(seed_csv_path / f'{category}.csv')
        assert counts[category] == len(df), f'{category} count mismatch vs CSV'


def test_seed_rows_origin_sample_and_org_scoped(
    client, db_session: Session, signup_workspace, seed_csv_path
):
    org_id, _ = signup_workspace()
    org_uuid = UUID(org_id)

    rows = db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == org_uuid)
    ).scalars().all()
    assert rows
    assert all(row.data_origin == 'sample' for row in rows)
    assert all(row.organization_id == org_uuid for row in rows)

    items = db_session.execute(
        select(Item).where(Item.organization_id == org_uuid)
    ).scalars().all()
    assert all(item.data_origin == 'sample' for item in items)

    fleet = db_session.execute(
        select(FleetAsset).where(FleetAsset.organization_id == org_uuid)
    ).scalars().all()
    assert all(f.data_origin == 'sample' for f in fleet)


def test_signup_seed_audit_event_recorded(
    client, db_session: Session, signup_workspace, seed_csv_path
):
    org_id, _ = signup_workspace()
    org_uuid = UUID(org_id)

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'workspace.seeded_sample_data')
    ).scalars().first()
    assert event is not None
    assert event.organization_id == org_uuid
    assert event.actor_user_id is not None
    assert event.created_at is not None

    payload = event.payload
    assert sorted(payload['categories']) == ['fleet_assets', 'inventory', 'items', 'orders', 'warehouses']
    rows = payload['rows_per_category']
    assert rows['warehouses'] > 0
    assert rows['orders'] > 0


def test_seed_idempotent_no_double_seed_on_second_org(
    client, db_session: Session, signup_workspace, seed_csv_path, sample_row_counts
):
    """§0A proof: two orgs both seeded with IDENTICAL sample CSVs, no
    IntegrityError, no cross-contamination."""
    org_a, _ = signup_workspace(name='Org A')
    org_b, _ = signup_workspace(name='Org B')

    counts_a = sample_row_counts(org_a)
    counts_b = sample_row_counts(org_b)
    assert counts_a == counts_b
    assert counts_a['warehouses'] > 0

    a_wh = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_a), Warehouse.code == 'WH-001'
        )
    ).scalar_one()
    b_wh = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_b), Warehouse.code == 'WH-001'
        )
    ).scalar_one()
    assert a_wh.id != b_wh.id
    assert a_wh.organization_id == UUID(org_a)
    assert b_wh.organization_id == UUID(org_b)


def test_seeded_workspace_runs_operations(client, signup_workspace, seed_csv_path):
    """NB-25.2: seeded workspace is fully operational without any upload."""
    _, token = signup_workspace()
    headers = {'Authorization': f'Bearer {token}'}

    opt = client.post('/api/v1/routes/optimize', headers=headers, json=_optimize_payload())
    assert opt.status_code == 200, opt.text

    forecast = client.post(
        '/api/v1/forecast/weekly-demand', headers=headers, json={'horizon_weeks': 4}
    )
    assert forecast.status_code == 200, forecast.text

    alert = client.post(
        '/api/v1/alerts',
        headers=headers,
        json={'alert_type': 'manual', 'severity': 'medium', 'title': 'Seed smoke', 'message': 'ops'},
    )
    assert alert.status_code == 201, alert.text
    ack = client.post(
        f"/api/v1/alerts/{alert.json()['id']}/acknowledge", headers=headers, json={'note': 'ok'}
    )
    assert ack.status_code == 200, ack.text


def test_supersede_warehouses_deletes_sample_warehouses(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    org_id, token = signup_workspace()
    before = _seed_counts(db_session, org_id)
    assert before['warehouses'] > 0

    resp = upload_csv(
        token,
        'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert resp.status_code == 200, resp.text

    sample_left = db_session.execute(
        select(func.count()).select_from(Warehouse).where(
            Warehouse.organization_id == UUID(org_id), Warehouse.data_origin == 'sample'
        )
    ).scalar_one()
    assert sample_left == 0

    real_rows = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_id), Warehouse.data_origin == 'real'
        )
    ).scalars().all()
    assert [w.code for w in real_rows] == ['WH-REAL-1']


def test_supersede_keeps_sample_warehouse_referenced_by_real_inventory(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """Decision #3 load-bearing guard: real inventory referencing a sample
    warehouse protects it from supersede deletion."""
    org_id, token = signup_workspace()

    inv = upload_csv(
        token,
        'inventory',
        content=real_inventory_csv([('WH-001', 'SKU-001', 100, 10)]),
    )
    assert inv.status_code == 200, inv.text

    real_inv = db_session.execute(
        select(Inventory).where(
            Inventory.organization_id == UUID(org_id), Inventory.data_origin == 'real'
        )
    ).scalars().all()
    assert len(real_inv) == 1
    kept_warehouse_id = real_inv[0].warehouse_id

    resp = upload_csv(
        token,
        'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert resp.status_code == 200, resp.text

    kept = db_session.get(Warehouse, kept_warehouse_id)
    assert kept is not None, 'sample warehouse referenced by real inventory was deleted'
    assert kept.data_origin == 'sample'

    remaining = db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == UUID(org_id))
    ).scalars().all()
    codes = {w.code for w in remaining}
    assert kept.code in codes
    assert 'WH-REAL-1' in codes


def test_supersede_deletes_dangling_sample_inventory_orders(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """Decision #3: sample inventory/orders referencing deleted sample
    warehouses are explicitly removed in the same transaction."""
    org_id, token = signup_workspace()
    assert _seed_counts(db_session, org_id)['inventory'] > 0

    resp = upload_csv(
        token,
        'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert resp.status_code == 200, resp.text

    sample_inv = db_session.execute(
        select(func.count()).select_from(Inventory).where(
            Inventory.organization_id == UUID(org_id), Inventory.data_origin == 'sample'
        )
    ).scalar_one()
    sample_orders = db_session.execute(
        select(func.count()).select_from(HistoricalOrder).where(
            HistoricalOrder.organization_id == UUID(org_id),
            HistoricalOrder.data_origin == 'sample',
        )
    ).scalar_one()
    assert sample_inv == 0
    assert sample_orders == 0


def test_upload_scoped_to_own_org_does_not_touch_other_org_rows(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    """Decision #13: org A's upload of WH-001 updates only org A's row."""
    org_a, token_a = signup_workspace(name='Org A')
    org_b, _ = signup_workspace(name='Org B')

    resp = upload_csv(
        token_a,
        'warehouses',
        content=real_warehouse_csv([
            ('WH-001', 'ORG A OWNED', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert resp.status_code == 200, resp.text

    a_wh = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_a), Warehouse.code == 'WH-001'
        )
    ).scalar_one()
    b_wh = db_session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == UUID(org_b), Warehouse.code == 'WH-001'
        )
    ).scalar_one()

    assert a_wh.data_origin == 'real'
    assert a_wh.name == 'ORG A OWNED'
    assert b_wh.data_origin == 'sample'
    assert b_wh.name != 'ORG A OWNED'


def test_upload_records_csv_upload_audit_event(
    client, db_session: Session, signup_workspace, seed_csv_path, upload_csv
):
    org_id, token = signup_workspace()
    resp = upload_csv(
        token,
        'items',
        content=real_items_csv([
            ('SKU-REAL-1', 'Real Item', 'Mechanical', 5.0, 2),
        ]),
    )
    assert resp.status_code == 200, resp.text

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'workspace.csv_uploaded')
    ).scalars().first()
    assert event is not None
    payload = event.payload
    assert payload['category'] == 'items'
    assert payload['data_origin'] == 'real'
    assert payload['records_created'] == 1
    assert payload['records_processed'] == 1
    assert payload['errors'] == []
