"""NB-86 — driver roster and cash-on-delivery reconciliation.

Written from the buyer's side of the desk. Each test states the operational
question it answers, because the point of these features is not that the
endpoints exist but that an operator can stop keeping this in a notebook:

- "Who has this load?"                        -> driver assignment
- "What has that driver got on the van?"      -> driver shipment list
- "How much cash should be coming back?"      -> cod_amount_etb
- "How much actually came back?"              -> declare / settle
- "How much never came back?"                 -> ledger shortfall
- "Did that confirmation get through?"        -> idempotency

Cross-tenant behaviour is pinned here too: cash is the most sensitive data in the
product, so a driver or a cash record from another organisation must be
indistinguishable from one that does not exist (404, never 403).
"""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cash_collection import CashCollection
from app.models.driver import Driver


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _make_driver(client: TestClient, token: str, name: str = 'Yohannes Bekele', phone: str = '+251911000001') -> dict:
    resp = client.post(
        '/api/v1/drivers',
        headers=_headers(token),
        json={'full_name': name, 'phone': phone, 'vehicle_plate': 'AA-3-B12345'},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_shipment(
    client: TestClient,
    token: str,
    shipment_no: str,
    *,
    driver_id: str | None = None,
    cod: str = '0.00',
    client_ref: str | None = None,
) -> dict:
    payload: dict = {
        'shipment_no': shipment_no,
        'origin_warehouse_code': 'WH-001',
        'destination_warehouse_code': 'WH-002',
        'sku': 'SKU-001',
        'quantity_units': 10,
        'cod_amount_etb': cod,
    }
    if driver_id:
        payload['driver_id'] = driver_id
    if client_ref:
        payload['client_ref'] = client_ref
    resp = client.post('/api/v1/shipments', headers=_headers(token), json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _deliver(client: TestClient, token: str, shipment_id: str, **extra) -> dict:
    body = {'status': 'delivered', **extra}
    resp = client.post(
        f'/api/v1/shipments/{shipment_id}/status', headers=_headers(token), json=body
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# The roster
# ---------------------------------------------------------------------------


def test_driver_can_be_added_and_appears_on_the_roster(
    client: TestClient, signup_workspace, seed_csv_path
):
    """The operator's first question in the morning: who is driving today?"""
    _, token = signup_workspace('Roster Co')
    _make_driver(client, token, 'Yohannes Bekele', '+251911000001')
    _make_driver(client, token, 'Marta Alemu', '+251911000002')

    resp = client.get('/api/v1/drivers', headers=_headers(token))
    assert resp.status_code == 200, resp.text
    names = [d['full_name'] for d in resp.json()]
    assert names == ['Marta Alemu', 'Yohannes Bekele'], 'roster is sorted by name'
    assert all(d['status'] == 'active' for d in resp.json())


def test_duplicate_phone_in_one_workspace_is_a_conflict(
    client: TestClient, signup_workspace, seed_csv_path
):
    """Phone is how a driver is actually identified, so it must not double up."""
    _, token = signup_workspace('Dupe Co')
    _make_driver(client, token, 'First Driver', '+251911000009')

    resp = client.post(
        '/api/v1/drivers',
        headers=_headers(token),
        json={'full_name': 'Second Driver', 'phone': '+251911000009'},
    )
    assert resp.status_code == 409
    assert 'phone' in resp.json()['detail'].lower()


def test_driver_can_be_updated_and_deactivated(
    client: TestClient, signup_workspace, seed_csv_path
):
    _, token = signup_workspace('Update Co')
    driver = _make_driver(client, token)

    resp = client.patch(
        f"/api/v1/drivers/{driver['id']}",
        headers=_headers(token),
        json={'vehicle_plate': 'AA-3-C99999', 'notes': 'Long-haul only'},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['vehicle_plate'] == 'AA-3-C99999'
    assert resp.json()['notes'] == 'Long-haul only'

    # Deactivation, not deletion: history must survive a leaver.
    resp = client.delete(f"/api/v1/drivers/{driver['id']}", headers=_headers(token))
    assert resp.status_code == 204, resp.text

    active = client.get('/api/v1/drivers?status=active', headers=_headers(token)).json()
    assert active == []
    everyone = client.get('/api/v1/drivers', headers=_headers(token)).json()
    assert len(everyone) == 1 and everyone[0]['status'] == 'inactive'


def test_inactive_driver_cannot_be_assigned(
    client: TestClient, signup_workspace, seed_csv_path
):
    """A driver who has left must not silently keep receiving work."""
    _, token = signup_workspace('Inactive Co')
    driver = _make_driver(client, token)
    client.delete(f"/api/v1/drivers/{driver['id']}", headers=_headers(token))

    resp = client.post(
        '/api/v1/shipments',
        headers=_headers(token),
        json={
            'shipment_no': 'SHP-INACTIVE',
            'origin_warehouse_code': 'WH-001',
            'destination_warehouse_code': 'WH-002',
            'sku': 'SKU-001',
            'quantity_units': 5,
            'driver_id': driver['id'],
        },
    )
    assert resp.status_code == 409
    assert 'not active' in resp.json()['detail']


# ---------------------------------------------------------------------------
# Assignment: who is carrying this
# ---------------------------------------------------------------------------


def test_shipment_can_be_assigned_and_reassigned(
    client: TestClient, signup_workspace, seed_csv_path
):
    _, token = signup_workspace('Assign Co')
    first = _make_driver(client, token, 'First Driver', '+251911000011')
    second = _make_driver(client, token, 'Second Driver', '+251911000012')
    shipment = _make_shipment(client, token, 'SHP-ASSIGN')

    assert shipment['driver_id'] is None

    resp = client.post(
        f"/api/v1/shipments/{shipment['id']}/driver",
        headers=_headers(token),
        json={'driver_id': first['id']},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['driver_name'] == 'First Driver'

    resp = client.post(
        f"/api/v1/shipments/{shipment['id']}/driver",
        headers=_headers(token),
        json={'driver_id': second['id']},
    )
    assert resp.json()['driver_name'] == 'Second Driver'

    # Clearing is a legitimate dispatch action (the job is cancelled/reassigned).
    resp = client.post(
        f"/api/v1/shipments/{shipment['id']}/driver",
        headers=_headers(token),
        json={'driver_id': None},
    )
    assert resp.json()['driver_id'] is None


def test_driver_shipment_list_answers_what_is_on_the_van(
    client: TestClient, signup_workspace, seed_csv_path
):
    _, token = signup_workspace('Van Co')
    driver = _make_driver(client, token)
    other = _make_driver(client, token, 'Other Driver', '+251911000021')

    _make_shipment(client, token, 'SHP-VAN-1', driver_id=driver['id'], cod='1500.00')
    _make_shipment(client, token, 'SHP-VAN-2', driver_id=driver['id'])
    _make_shipment(client, token, 'SHP-VAN-3', driver_id=other['id'])

    resp = client.get(f"/api/v1/drivers/{driver['id']}/shipments", headers=_headers(token))
    assert resp.status_code == 200, resp.text
    numbers = sorted(s['shipment_no'] for s in resp.json())
    assert numbers == ['SHP-VAN-1', 'SHP-VAN-2'], 'only this driver’s work'
    assert resp.json()[0]['cod_amount_etb'] in ('1500.00', '0.00')


# ---------------------------------------------------------------------------
# Cash on delivery
# ---------------------------------------------------------------------------


def test_delivery_with_no_cash_declared_leaves_the_full_amount_outstanding(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """Goods handed over, cash not yet handed in: the risk is now visible."""
    _, token = signup_workspace('Outstanding Co')
    driver = _make_driver(client, token)
    shipment = _make_shipment(client, token, 'SHP-COD-1', driver_id=driver['id'], cod='2500.00')

    _deliver(client, token, shipment['id'])

    rows = db_session.execute(select(CashCollection)).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == 'outstanding'
    assert rows[0].expected_etb == Decimal('2500.00')
    assert rows[0].collected_etb == Decimal('0.00')
    assert rows[0].shortfall_etb == Decimal('2500.00')
    assert rows[0].driver_id is not None


def test_cash_declared_with_delivery_records_the_shortfall(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """The real-world case: the customer paid part of it."""
    _, token = signup_workspace('Shortfall Co')
    shipment = _make_shipment(client, token, 'SHP-COD-2', cod='2500.00')

    _deliver(client, token, shipment['id'], cash_collected_etb='2000.00', cash_note='Customer short')

    record = db_session.execute(select(CashCollection)).scalar_one()
    assert record.status == 'collected'
    assert record.collected_etb == Decimal('2000.00')
    assert record.shortfall_etb == Decimal('500.00')
    assert record.collected_at is not None


def test_exact_cash_leaves_no_shortfall(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    _, token = signup_workspace('Exact Co')
    shipment = _make_shipment(client, token, 'SHP-COD-3', cod='1200.50')

    _deliver(client, token, shipment['id'], cash_collected_etb='1200.50')

    record = db_session.execute(select(CashCollection)).scalar_one()
    assert record.shortfall_etb == Decimal('0.00')
    assert record.status == 'collected'


def test_over_collection_is_a_surplus_not_a_negative_shortfall(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """A driver who collects more is visible as a surplus; shortfall stays floored."""
    _, token = signup_workspace('Surplus Co')
    shipment = _make_shipment(client, token, 'SHP-COD-4', cod='1000.00')

    _deliver(client, token, shipment['id'], cash_collected_etb='1100.00')

    record = db_session.execute(select(CashCollection)).scalar_one()
    assert record.shortfall_etb == Decimal('0.00')
    assert record.collected_etb == Decimal('1100.00')


def test_cash_declared_without_delivery_is_rejected(
    client: TestClient, signup_workspace, seed_csv_path
):
    """Cash cannot change hands on a shipment that was not delivered."""
    _, token = signup_workspace('BadCash Co')
    shipment = _make_shipment(client, token, 'SHP-COD-5', cod='800.00')

    resp = client.post(
        f"/api/v1/shipments/{shipment['id']}/status",
        headers=_headers(token),
        json={'status': 'in_transit', 'cash_collected_etb': '800.00'},
    )
    assert resp.status_code == 400
    assert 'delivered' in resp.json()['detail']


def test_shipment_without_cod_opens_no_cash_record(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """No cash expected means no ledger noise for the office to clear."""
    _, token = signup_workspace('NoCod Co')
    shipment = _make_shipment(client, token, 'SHP-COD-6', cod='0.00')

    _deliver(client, token, shipment['id'])

    assert db_session.execute(select(CashCollection)).scalars().all() == []


# ---------------------------------------------------------------------------
# The ledger: end-of-day reconciliation
# ---------------------------------------------------------------------------


def test_ledger_summarises_what_is_out_and_what_is_missing(
    client: TestClient, signup_workspace, seed_csv_path
):
    """The end-of-day number an operator actually needs."""
    _, token = signup_workspace('Ledger Co')

    outstanding = _make_shipment(client, token, 'SHP-L-1', cod='1000.00')
    short = _make_shipment(client, token, 'SHP-L-2', cod='2000.00')

    _deliver(client, token, outstanding['id'])
    _deliver(client, token, short['id'], cash_collected_etb='1500.00')

    resp = client.get('/api/v1/cash-collections/ledger', headers=_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body['outstanding_count'] == 1
    assert Decimal(body['outstanding_expected_etb']) == Decimal('1000.00')
    assert body['collected_count'] == 1
    assert Decimal(body['collected_etb']) == Decimal('1500.00')
    # 1000 still fully out + 500 missing from the second
    assert Decimal(body['shortfall_etb']) == Decimal('1500.00')


def test_declare_then_settle_closes_the_record_but_keeps_the_shortfall(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """A written-off shortfall is the number an operator needs at month end, so
    settling must not erase it."""
    _, token = signup_workspace('Settle Co')
    shipment = _make_shipment(client, token, 'SHP-L-3', cod='3000.00')
    _deliver(client, token, shipment['id'])

    record = db_session.execute(select(CashCollection)).scalar_one()
    record_id = str(record.id)

    resp = client.post(
        f'/api/v1/cash-collections/{record_id}/declare',
        headers=_headers(token),
        json={'collected_etb': '2800.00', 'note': 'Customer withheld 200'},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['status'] == 'collected'
    assert Decimal(resp.json()['shortfall_etb']) == Decimal('200.00')

    resp = client.post(
        f'/api/v1/cash-collections/{record_id}/settle',
        headers=_headers(token),
        json={'note': 'Banked, 200 written off'},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()['status'] == 'settled'
    assert Decimal(resp.json()['shortfall_etb']) == Decimal('200.00')
    assert resp.json()['settled_at'] is not None

    # Settled records are summary-visible but no longer outstanding.
    ledger = client.get('/api/v1/cash-collections/ledger', headers=_headers(token)).json()
    assert ledger['settled_count'] == 1
    assert ledger['outstanding_count'] == 0


def test_settled_record_cannot_be_reopened_by_a_replayed_delivery(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """The dangerous retry: a confirmation arriving after the cash was banked.

    It must not resurrect the debt — the record is closed and stays closed.
    """
    _, token = signup_workspace('Replay Co')
    shipment = _make_shipment(client, token, 'SHP-L-4', cod='900.00')
    _deliver(client, token, shipment['id'], cash_collected_etb='900.00')

    record = db_session.execute(select(CashCollection)).scalar_one()
    record_id = str(record.id)
    client.post(
        f'/api/v1/cash-collections/{record_id}/settle', headers=_headers(token), json={}
    )

    far_past = '2020-01-01T00:00:00+00:00'
    _deliver(client, token, shipment['id'], cash_collected_etb='0.00', actual_delivery=far_past)

    db_session.expire_all()
    record = db_session.execute(select(CashCollection)).scalar_one()
    assert record.status == 'settled', 'a late retry must not reopen settled cash'
    assert record.shortfall_etb == Decimal('0.00')
    assert record.settled_at is not None


def test_declaring_twice_is_idempotent(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """A retry after a dropped connection must not double-count."""
    _, token = signup_workspace('Idem Co')
    shipment = _make_shipment(client, token, 'SHP-L-5', cod='700.00')
    _deliver(client, token, shipment['id'])

    record_id = str(db_session.execute(select(CashCollection)).scalar_one().id)
    for _ in range(3):
        resp = client.post(
            f'/api/v1/cash-collections/{record_id}/declare',
            headers=_headers(token),
            json={'collected_etb': '700.00'},
        )
        assert resp.status_code == 200, resp.text

    db_session.expire_all()
    rows = db_session.execute(select(CashCollection)).scalars().all()
    assert len(rows) == 1, 'one cash record per shipment, always'
    assert rows[0].collected_etb == Decimal('700.00')
    assert rows[0].shortfall_etb == Decimal('0.00')


def test_settling_requires_admin(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session, viewer_token: str
):
    """Writing off money is not an operator- or viewer-level action.

    Settling is admin-only for the same reason receipt reversal is: it accepts a
    shortfall, which writes money off the books.
    """
    _, token = signup_workspace('Role Co')
    shipment = _make_shipment(client, token, 'SHP-L-6', cod='500.00')
    _deliver(client, token, shipment['id'])
    record_id = str(db_session.execute(select(CashCollection)).scalar_one().id)

    # A viewer may read the ledger but must not close a record.
    assert client.get('/api/v1/cash-collections', headers=_headers(viewer_token)).status_code == 200
    resp = client.post(
        f'/api/v1/cash-collections/{record_id}/settle',
        headers=_headers(viewer_token),
        json={},
    )
    assert resp.status_code == 403, resp.text

    # Delivered with no cash declared, so the record is still outstanding — and the
    # rejected settle must have changed nothing.
    db_session.expire_all()
    assert db_session.execute(select(CashCollection)).scalar_one().status == 'outstanding'


# ---------------------------------------------------------------------------
# Idempotent create: the dropped-connection case
# ---------------------------------------------------------------------------


def test_repeated_create_with_the_same_client_ref_returns_one_shipment(
    client: TestClient, signup_workspace, seed_csv_path
):
    """A dispatch screen that retries must not create the load twice."""
    _, token = signup_workspace('Ref Co')

    first = _make_shipment(client, token, 'SHP-R-1', client_ref='dispatch-abc-123', cod='400.00')
    second = _make_shipment(client, token, 'SHP-R-1', client_ref='dispatch-abc-123', cod='400.00')

    assert first['id'] == second['id'], 'the retry resolved to the same shipment'

    listing = client.get('/api/v1/shipments', headers=_headers(token)).json()
    assert len([s for s in listing if s['client_ref'] == 'dispatch-abc-123']) == 1


def test_client_ref_is_scoped_per_organisation(
    client: TestClient, signup_workspace, seed_csv_path
):
    """Two companies may independently use the same reference without colliding."""
    _, token_a = signup_workspace('Ref A')
    _, token_b = signup_workspace('Ref B')

    a = _make_shipment(client, token_a, 'SHP-RA-1', client_ref='shared-ref-1')
    b = _make_shipment(client, token_b, 'SHP-RB-1', client_ref='shared-ref-1')

    assert a['id'] != b['id']


def test_reassignment_follows_the_cash(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """Cash accountability follows the driver, not whoever was assigned first."""
    _, token = signup_workspace('Follow Co')
    first = _make_driver(client, token, 'First Driver', '+251911000031')
    second = _make_driver(client, token, 'Second Driver', '+251911000032')
    shipment = _make_shipment(client, token, 'SHP-F-1', driver_id=first['id'], cod='600.00')
    _deliver(client, token, shipment['id'])

    record = db_session.execute(select(CashCollection)).scalar_one()
    assert str(record.driver_id) == first['id']

    client.post(
        f"/api/v1/shipments/{shipment['id']}/driver",
        headers=_headers(token),
        json={'driver_id': second['id']},
    )

    db_session.expire_all()
    record = db_session.execute(select(CashCollection)).scalar_one()
    assert str(record.driver_id) == second['id'], 'the ledger points at who holds the cash now'


# ---------------------------------------------------------------------------
# Tenant isolation — cash is the most sensitive data here
# ---------------------------------------------------------------------------


def test_drivers_are_invisible_across_organisations(
    client: TestClient, signup_workspace, seed_csv_path
):
    _, token_a = signup_workspace('Drv Iso A')
    _, token_b = signup_workspace('Drv Iso B')

    a_driver = _make_driver(client, token_a, 'A Driver', '+251911111111')

    assert client.get('/api/v1/drivers', headers=_headers(token_b)).json() == []
    # 404, never 403: existence must not leak.
    assert client.get(f"/api/v1/drivers/{a_driver['id']}", headers=_headers(token_b)).status_code == 404
    assert (
        client.patch(
            f"/api/v1/drivers/{a_driver['id']}", headers=_headers(token_b), json={'notes': 'x'}
        ).status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/drivers/{a_driver['id']}/shipments", headers=_headers(token_b)).status_code
        == 404
    )


def test_cannot_assign_another_organisations_driver(
    client: TestClient, signup_workspace, seed_csv_path
):
    """Assigning a foreign driver would leak the row and misattribute cash."""
    _, token_a = signup_workspace('Cross A')
    _, token_b = signup_workspace('Cross B')

    a_driver = _make_driver(client, token_a, 'A Driver', '+251922222222')
    b_shipment = _make_shipment(client, token_b, 'SHP-CROSS-1')

    resp = client.post(
        f"/api/v1/shipments/{b_shipment['id']}/driver",
        headers=_headers(token_b),
        json={'driver_id': a_driver['id']},
    )
    assert resp.status_code == 404, resp.text


def test_cash_records_are_invisible_across_organisations(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    _, token_a = signup_workspace('Cash Iso A')
    _, token_b = signup_workspace('Cash Iso B')

    shipment = _make_shipment(client, token_a, 'SHP-CI-1', cod='1000.00')
    _deliver(client, token_a, shipment['id'])
    record_id = str(db_session.execute(select(CashCollection)).scalar_one().id)

    assert client.get('/api/v1/cash-collections', headers=_headers(token_b)).json() == []
    assert client.get(f'/api/v1/cash-collections/{record_id}', headers=_headers(token_b)).status_code == 404
    assert (
        client.post(
            f'/api/v1/cash-collections/{record_id}/declare',
            headers=_headers(token_b),
            json={'collected_etb': '1.00'},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f'/api/v1/cash-collections/{record_id}/settle', headers=_headers(token_b), json={}
        ).status_code
        == 404
    )

    # And org B's ledger stays empty rather than including A's exposure.
    ledger = client.get('/api/v1/cash-collections/ledger', headers=_headers(token_b)).json()
    assert Decimal(ledger['shortfall_etb']) == Decimal('0.00')
    assert ledger['outstanding_count'] == 0


def test_driver_rows_carry_the_creating_organisation(
    client: TestClient, signup_workspace, seed_csv_path, db_session: Session
):
    """Guards the scoping column itself: a NULL here would make the roster global."""
    org_id, token = signup_workspace('Org Stamp Co')
    _make_driver(client, token)

    driver = db_session.execute(select(Driver)).scalar_one()
    assert str(driver.organization_id) == org_id
