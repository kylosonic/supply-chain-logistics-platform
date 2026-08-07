"""TECH-58 — tenant isolation for warehouses/items CRUD (blueprint §7.2).

All four endpoints per resource become org-scoped: list filters by actor
org (+ legacy null-org rows via ``is_(None)``), create stamps
``organization_id`` and duplicate pre-checks equality-only, get/update
guard cross-org reads with 404. Org-less actors keep the unfiltered
pass-through contract.
"""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.warehouse import Warehouse


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _warehouse_payload(code: str, **overrides: object) -> dict:
    payload = {
        'code': code,
        'name': f'WH {code}',
        'address': 'Addr',
        'city': 'City',
        'state': 'State',
        'country': 'ET',
        'latitude': 9.0,
        'longitude': 38.8,
        'capacity_units': 1000,
    }
    payload.update(overrides)
    return payload


def _item_payload(sku: str, **overrides: object) -> dict:
    payload = {
        'sku': sku,
        'name': f'Item {sku}',
        'category': 'Mechanical',
        'unit_cost': 12.5,
        'reorder_level': 10,
    }
    payload.update(overrides)
    return payload


def _org_ids(db: Session, org_id: str) -> set[UUID]:
    return {w.organization_id for w in db.execute(select(Warehouse)).scalars()}


# ---------------------------------------------------------------------------
# Warehouses
# ---------------------------------------------------------------------------


def test_list_warehouses_org_a_sees_only_own_rows(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    resp = client.get('/api/v1/warehouses', headers=_headers(token_a))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3
    assert {r['code'] for r in rows} == {'WH-001', 'WH-002', 'WH-003'}
    a_ids = {
        str(w.id)
        for w in db_session.execute(
            select(Warehouse).where(Warehouse.organization_id == UUID(org_a))
        ).scalars()
    }
    assert {r['id'] for r in rows} == a_ids
    assert _org_ids(db_session, org_a) == {UUID(org_a), UUID(org_b)}

    resp_b = client.get('/api/v1/warehouses', headers=_headers(token_b))
    assert resp_b.status_code == 200
    rows_b = resp_b.json()
    assert len(rows_b) == 3
    assert {r['code'] for r in rows_b} == {'WH-001', 'WH-002', 'WH-003'}
    b_ids = {
        str(w.id)
        for w in db_session.execute(
            select(Warehouse).where(Warehouse.organization_id == UUID(org_b))
        ).scalars()
    }
    assert {r['id'] for r in rows_b} == b_ids
    assert a_ids.isdisjoint(b_ids)


def test_get_warehouse_from_other_org_returns_404(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    b_id = db_session.execute(
        select(Warehouse.id).where(Warehouse.organization_id == UUID(org_b))
    ).scalars().first()
    assert b_id is not None

    resp = client.get(f'/api/v1/warehouses/{b_id}', headers=_headers(token_a))
    assert resp.status_code == 404
    assert resp.json()['detail'] == 'Warehouse not found'

    a_id = db_session.execute(
        select(Warehouse.id).where(Warehouse.organization_id == UUID(org_a))
    ).scalars().first()
    own = client.get(f'/api/v1/warehouses/{a_id}', headers=_headers(token_a))
    assert own.status_code == 200


def test_create_warehouse_stamps_organization_id(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')

    resp = client.post(
        '/api/v1/warehouses', headers=_headers(token_a), json=_warehouse_payload('WH-Z9')
    )
    assert resp.status_code == 201, resp.text

    row = db_session.execute(
        select(Warehouse).where(Warehouse.code == 'WH-Z9')
    ).scalar_one()
    assert row.organization_id == UUID(org_a)
    assert row.data_origin == 'real'


def test_create_warehouse_duplicate_code_same_org_returns_409(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Iso A')

    first = client.post(
        '/api/v1/warehouses', headers=_headers(token_a), json=_warehouse_payload('WH-Z9')
    )
    assert first.status_code == 201, first.text
    second = client.post(
        '/api/v1/warehouses', headers=_headers(token_a), json=_warehouse_payload('WH-Z9')
    )
    assert second.status_code == 409
    assert second.json()['detail'] == 'Warehouse code already exists'

    seeded = client.post(
        '/api/v1/warehouses', headers=_headers(token_a), json=_warehouse_payload('WH-001')
    )
    assert seeded.status_code == 409
    assert seeded.json()['detail'] == 'Warehouse code already exists'


def test_create_warehouse_duplicate_code_other_org_returns_201(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    first = client.post(
        '/api/v1/warehouses', headers=_headers(token_a), json=_warehouse_payload('WH-Z9')
    )
    assert first.status_code == 201, first.text

    resp = client.post(
        '/api/v1/warehouses', headers=_headers(token_b), json=_warehouse_payload('WH-Z9')
    )
    assert resp.status_code == 201, resp.text
    row = db_session.execute(
        select(Warehouse).where(Warehouse.code == 'WH-Z9', Warehouse.organization_id == UUID(org_b))
    ).scalar_one()
    assert row.organization_id == UUID(org_b)


def test_update_warehouse_other_org_returns_404_and_own_200(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    b_id = db_session.execute(
        select(Warehouse.id).where(Warehouse.organization_id == UUID(org_b))
    ).scalars().first()

    resp = client.patch(
        f'/api/v1/warehouses/{b_id}',
        headers=_headers(token_a),
        json={'name': 'Hijacked'},
    )
    assert resp.status_code == 404
    assert resp.json()['detail'] == 'Warehouse not found'

    a_id = db_session.execute(
        select(Warehouse.id).where(Warehouse.organization_id == UUID(org_a))
    ).scalars().first()
    own = client.patch(
        f'/api/v1/warehouses/{a_id}',
        headers=_headers(token_a),
        json={'name': 'Renamed Own'},
    )
    assert own.status_code == 200
    row = db_session.get(Warehouse, a_id)
    assert row.name == 'Renamed Own'


# ---------------------------------------------------------------------------
# Items — mirror the warehouse matrix
# ---------------------------------------------------------------------------


def test_list_items_org_a_sees_only_own_rows(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    resp = client.get('/api/v1/items', headers=_headers(token_a))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3
    assert {r['sku'] for r in rows} == {'SKU-001', 'SKU-002', 'SKU-003'}
    a_ids = {
        str(i.id)
        for i in db_session.execute(
            select(Item).where(Item.organization_id == UUID(org_a))
        ).scalars()
    }
    assert {r['id'] for r in rows} == a_ids
    db_orgs = {i.organization_id for i in db_session.execute(select(Item)).scalars()}
    assert db_orgs == {UUID(org_a), UUID(org_b)}

    resp_b = client.get('/api/v1/items', headers=_headers(token_b))
    assert resp_b.status_code == 200
    rows_b = resp_b.json()
    assert len(rows_b) == 3
    assert {r['sku'] for r in rows_b} == {'SKU-001', 'SKU-002', 'SKU-003'}
    b_ids = {
        str(i.id)
        for i in db_session.execute(
            select(Item).where(Item.organization_id == UUID(org_b))
        ).scalars()
    }
    assert {r['id'] for r in rows_b} == b_ids
    assert a_ids.isdisjoint(b_ids)


def test_get_item_from_other_org_returns_404(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    b_id = db_session.execute(
        select(Item.id).where(Item.organization_id == UUID(org_b))
    ).scalars().first()
    assert b_id is not None

    resp = client.get(f'/api/v1/items/{b_id}', headers=_headers(token_a))
    assert resp.status_code == 404
    assert resp.json()['detail'] == 'Item not found'

    a_id = db_session.execute(
        select(Item.id).where(Item.organization_id == UUID(org_a))
    ).scalars().first()
    own = client.get(f'/api/v1/items/{a_id}', headers=_headers(token_a))
    assert own.status_code == 200


def test_create_item_stamps_organization_id(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')

    resp = client.post(
        '/api/v1/items', headers=_headers(token_a), json=_item_payload('SKU-Z9')
    )
    assert resp.status_code == 201, resp.text

    row = db_session.execute(select(Item).where(Item.sku == 'SKU-Z9')).scalar_one()
    assert row.organization_id == UUID(org_a)
    assert row.data_origin == 'real'


def test_create_item_duplicate_sku_same_org_returns_409(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Iso A')

    first = client.post(
        '/api/v1/items', headers=_headers(token_a), json=_item_payload('SKU-Z9')
    )
    assert first.status_code == 201, first.text
    second = client.post(
        '/api/v1/items', headers=_headers(token_a), json=_item_payload('SKU-Z9')
    )
    assert second.status_code == 409
    assert second.json()['detail'] == 'SKU already exists'

    seeded = client.post(
        '/api/v1/items', headers=_headers(token_a), json=_item_payload('SKU-001')
    )
    assert seeded.status_code == 409
    assert seeded.json()['detail'] == 'SKU already exists'


def test_create_item_duplicate_sku_other_org_returns_201(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    first = client.post(
        '/api/v1/items', headers=_headers(token_a), json=_item_payload('SKU-Z9')
    )
    assert first.status_code == 201, first.text

    resp = client.post(
        '/api/v1/items', headers=_headers(token_b), json=_item_payload('SKU-Z9')
    )
    assert resp.status_code == 201, resp.text
    row = db_session.execute(
        select(Item).where(Item.sku == 'SKU-Z9', Item.organization_id == UUID(org_b))
    ).scalar_one()
    assert row.organization_id == UUID(org_b)


def test_update_item_other_org_returns_404_and_own_200(
    client: TestClient, db_session: Session, signup_workspace, seed_csv_path
):
    org_a, token_a = signup_workspace('Iso A')
    org_b, token_b = signup_workspace('Iso B')

    b_id = db_session.execute(
        select(Item.id).where(Item.organization_id == UUID(org_b))
    ).scalars().first()

    resp = client.patch(
        f'/api/v1/items/{b_id}',
        headers=_headers(token_a),
        json={'name': 'Hijacked'},
    )
    assert resp.status_code == 404
    assert resp.json()['detail'] == 'Item not found'

    a_id = db_session.execute(
        select(Item.id).where(Item.organization_id == UUID(org_a))
    ).scalars().first()
    own = client.patch(
        f'/api/v1/items/{a_id}',
        headers=_headers(token_a),
        json={'name': 'Renamed Own'},
    )
    assert own.status_code == 200
    row = db_session.get(Item, a_id)
    assert row.name == 'Renamed Own'
