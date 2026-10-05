"""Regression tests for two production defects found on 2026-10-05.

1. ``GET /api/v1/inventory`` answered **HTTP 500 for every tenant**.
   ``InventoryRead`` declared ``id`` / ``warehouse_id`` / ``item_id`` as ``str``
   while the model returns ``UUID``; Pydantic does not coerce one to the other, so
   serialising a real row raised ``ResponseValidationError``. Nothing caught it
   because the endpoint had no test and the console reads
   ``/inventory/overview`` instead — that projection carries no ids.

2. ``GET /api/v1/invoices`` carried **no tenant scope at all**, and
   ``POST /api/v1/invoices/upload`` never stamped ``organization_id``. Verified
   against production: a freshly created workspace that had never uploaded
   anything returned two freight invoices belonging to another tenant, while
   ``/notifications`` correctly returned none for the same caller.

Both are asserted from the operator's point of view: what a workspace can see,
and what it cannot.
"""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.freight_invoice import FreightInvoice
from app.models.order import HistoricalOrder


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _first_order(session: Session, org_id: str) -> HistoricalOrder:
    order = session.execute(
        select(HistoricalOrder).where(HistoricalOrder.organization_id == UUID(org_id))
    ).scalars().first()
    assert order is not None, 'a signed-up workspace always seeds historical orders'
    return order


def _invoice_csv(order_id: str, carrier: str = 'CARRIER-001', rate: str = '1000.00') -> str:
    return f'order_id,carrier_id,actual_rate\n{order_id},{carrier},{rate}\n'


# ---------------------------------------------------------------------------
# 1. Inventory serialisation (the 500)
# ---------------------------------------------------------------------------


def test_inventory_list_answers_for_a_seeded_workspace(client: TestClient, signup_workspace):
    """The regression: this was a 500, not an empty list."""
    _org_id, token = signup_workspace('Inventory Co')

    resp = client.get('/api/v1/inventory', headers=_auth(token))

    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 9, '3 seeded warehouses x 3 seeded SKUs'
    assert all(row['quantity_on_hand'] >= 0 for row in rows)


def test_inventory_ids_serialise_as_strings(client: TestClient, signup_workspace):
    """Pins the exact cause: UUID columns rendered through ``str`` fields."""
    _org_id, token = signup_workspace('Inventory Ids Co')

    rows = client.get('/api/v1/inventory', headers=_auth(token)).json()

    for row in rows:
        assert isinstance(row['id'], str)
        assert isinstance(row['warehouse_id'], str)
        assert isinstance(row['item_id'], str)
        # A UUID string, not a Python repr of a UUID object.
        UUID(row['id'])
        UUID(row['warehouse_id'])
        UUID(row['item_id'])


def test_inventory_overview_still_answers(client: TestClient, signup_workspace):
    """The projection the console actually reads must not regress."""
    _org_id, token = signup_workspace('Inventory Overview Co')

    resp = client.get('/api/v1/inventory/overview', headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 3


def test_inventory_is_not_visible_across_workspaces(client: TestClient):
    """The list is scoped to the caller's own workspace."""
    resp_a = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': 'Inv A',
            'company_email': 'owner@inva.com',
            'password': 'VeryStrongPass9',
            'subscription_tier': 'free',
        },
    )
    resp_b = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': 'Inv B',
            'company_email': 'owner@invb.com',
            'password': 'VeryStrongPass9',
            'subscription_tier': 'free',
        },
    )
    assert resp_a.status_code == 201 and resp_b.status_code == 201
    token_a = resp_a.json()['access_token']
    token_b = resp_b.json()['access_token']

    ids_a = {row['id'] for row in client.get('/api/v1/inventory', headers=_auth(token_a)).json()}
    ids_b = {row['id'] for row in client.get('/api/v1/inventory', headers=_auth(token_b)).json()}

    assert ids_a and ids_b, 'both workspaces are seeded'
    assert ids_a.isdisjoint(ids_b), 'no inventory row is shared between workspaces'


# ---------------------------------------------------------------------------
# 2. Freight invoices: tenant scope on read, ownership on write
# ---------------------------------------------------------------------------


def test_invoice_upload_stamps_the_owning_workspace(
    client: TestClient, db_session: Session, signup_workspace
):
    """An unattributed invoice is what made every historical row readable by all."""
    org_a, token_a = signup_workspace('Stamp Co')
    order = _first_order(db_session, org_a)

    resp = client.post(
        '/api/v1/invoices/upload',
        headers=_auth(token_a),
        files={'file': ('invoices.csv', _invoice_csv(str(order.id)).encode(), 'text/csv')},
    )

    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1

    stored = db_session.execute(select(FreightInvoice)).scalars().all()
    assert len(stored) == 1
    assert stored[0].organization_id == UUID(org_a)


def test_freight_invoices_are_not_visible_across_workspaces(
    client: TestClient, db_session: Session, signup_workspace
):
    org_a, token_a = signup_workspace('Invoice A')
    _org_b, token_b = signup_workspace('Invoice B')
    order = _first_order(db_session, org_a)

    uploaded = client.post(
        '/api/v1/invoices/upload',
        headers=_auth(token_a),
        files={'file': ('invoices.csv', _invoice_csv(str(order.id)).encode(), 'text/csv')},
    )
    assert uploaded.status_code == 200, uploaded.text

    mine = client.get('/api/v1/invoices', headers=_auth(token_a))
    assert mine.status_code == 200
    assert [row['carrier_id'] for row in mine.json()] == ['CARRIER-001']

    theirs = client.get('/api/v1/invoices', headers=_auth(token_b))
    assert theirs.status_code == 200, theirs.text
    assert theirs.json() == [], 'a workspace never sees another workspace freight invoices'


def test_invoice_upload_cannot_reconcile_against_another_workspaces_order(
    client: TestClient, db_session: Session, signup_workspace
):
    """The write-path leak: the order lookup had no tenant scope either."""
    org_a, token_a = signup_workspace('Order Owner Co')
    _org_b, token_b = signup_workspace('Order Stranger Co')
    order = _first_order(db_session, org_a)

    stolen = client.post(
        '/api/v1/invoices/upload',
        headers=_auth(token_b),
        files={'file': ('invoices.csv', _invoice_csv(str(order.id), carrier='STRANGER').encode(), 'text/csv')},
    )

    assert stolen.status_code == 200, stolen.text
    assert stolen.json() == [], 'the foreign order is filtered out, so nothing is created'

    assert client.get('/api/v1/invoices', headers=_auth(token_b)).json() == []
    assert client.get('/api/v1/invoices', headers=_auth(token_a)).json() == []


def test_freight_invoice_upload_rejects_a_missing_column(client: TestClient, signup_workspace):
    """Unchanged contract, pinned so the scoping edit did not disturb it."""
    _org_id, token = signup_workspace('Bad Column Co')

    resp = client.post(
        '/api/v1/invoices/upload',
        headers=_auth(token),
        files={'file': ('invoices.csv', b'order_id,carrier_id\nabc,CARRIER-001\n', 'text/csv')},
    )

    assert resp.status_code == 400
    assert 'actual_rate' in resp.json()['detail']
