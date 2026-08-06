"""Phase 4 free-cap lock tests (blueprint §10.2 — test_free_cap_lock.py, NB-31).

Composition inside ``require_writable_workspace`` (decision #5): the exact
disabled/available endpoint sets, no-overage, sample/real parity, month
rollover auto-lift, phase-lock priority, upgrade carve-out, receipts
exempt, and the 423 detail shape.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription_invoice import SubscriptionInvoice
from tests.conftest import real_warehouse_csv

_OPTIMIZE = {
    'route_name': 'Cap Route',
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


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _activation_free_cap(client, token: str) -> dict:
    resp = client.get('/api/v1/activation', headers=_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()['free_cap']


def test_cap_hit_delivery_tasks_disables_writes(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage, upload_csv
):
    """NB-31.2 full disabled list: optimize, upload, alert ack, replenishment
    approve, shipment create, provider set, manual alert."""
    org_id, token = signup_workspace()

    # Pre-lock artifacts: an alert to acknowledge, a plan to approve.
    alert = client.post(
        '/api/v1/alerts', headers=_headers(token),
        json={
            'alert_type': 'manual',
            'severity': 'medium',
            'title': 'Lock test',
            'message': 'lock test alert',
        },
    )
    assert alert.status_code == 201, alert.text
    alert_id = alert.json()['id']
    plan = client.post(
        '/api/v1/planning/replenishment/generate', headers=_headers(token), json={'horizon_weeks': 4}
    )
    assert plan.status_code == 200, plan.text
    plan_id = plan.json()[0]['id']

    advance_usage(org_id, 'delivery_tasks', 2500)

    assert _activation_free_cap(client, token)['locked'] is True

    optimize = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert optimize.status_code == 423
    assert optimize.json()['detail']['free_cap_locked'] is True

    upload = upload_csv(
        token, 'warehouses',
        content=real_warehouse_csv([
            ('WH-REAL-1', 'Real WH', '1 Rd', 'Addis', 'AA', 'Ethiopia', 9.0, 38.7, 100),
        ]),
    )
    assert upload.status_code == 423

    ack = client.post(
        f'/api/v1/alerts/{alert_id}/acknowledge', headers=_headers(token), json={'note': 'ack note'}
    )
    assert ack.status_code == 423
    resolve = client.post(
        f'/api/v1/alerts/{alert_id}/resolve', headers=_headers(token), json={'note': 'res note'}
    )
    assert resolve.status_code == 423

    approve = client.post(
        f'/api/v1/planning/replenishment/{plan_id}/approve', headers=_headers(token), json={}
    )
    assert approve.status_code == 423
    reject = client.post(
        f'/api/v1/planning/replenishment/{plan_id}/reject',
        headers=_headers(token),
        json={'reason': 'bad plan'},
    )
    assert reject.status_code == 423

    shipment = client.post(
        '/api/v1/shipments', headers=_headers(token),
        json={
            'shipment_no': 'SHP-LOCK-1',
            'origin_warehouse_code': 'WH-001',
            'destination_warehouse_code': 'WH-002',
            'sku': 'SKU-001',
            'quantity_units': 5,
        },
    )
    assert shipment.status_code == 423

    provider = client.post(
        '/api/v1/providers/keys', headers=_headers(token),
        json={'provider_name': 'mock', 'key_name': 'primary', 'api_key': 'sk-mock-1'},
    )
    assert provider.status_code == 423

    manual_alert = client.post(
        '/api/v1/alerts', headers=_headers(token),
        json={'alert_type': 'manual', 'severity': 'low', 'title': 'Blocked', 'message': 'blocked alert'},
    )
    assert manual_alert.status_code == 423

    forecast = client.post(
        '/api/v1/forecast/weekly-demand', headers=_headers(token), json={'horizon_weeks': 4}
    )
    assert forecast.status_code == 423


def test_cap_hit_route_optimizations_disables_writes(
    client, signup_workspace, seed_csv_path, advance_usage
):
    org_id, token = signup_workspace()
    advance_usage(org_id, 'route_optimizations', 50)

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 423
    assert resp.json()['detail']['free_cap_locked'] is True


def test_reads_remain_available(client, signup_workspace, seed_csv_path, advance_usage):
    """NB-31.3: reads/account/audit stay available while locked."""
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 2500)

    available = [
        ('GET', '/api/v1/activation', None),
        ('GET', '/api/v1/billing/state', None),
        ('GET', '/api/v1/routes/schedules', None),
        ('GET', '/api/v1/routes/history', None),
        ('GET', '/api/v1/subscriptions/me', None),
        ('GET', '/api/v1/subscriptions/usage/me', None),
        ('GET', '/api/v1/ops/audit-timeline', None),
        ('GET', '/api/v1/ops/exception-feed', None),
        ('GET', '/api/v1/ops/dock-appointments', None),
        ('GET', '/api/v1/alerts', None),
        ('GET', '/api/v1/shipments', None),
        ('GET', '/api/v1/inventory/overview', None),
        ('GET', '/api/v1/warehouses', None),
        ('GET', '/api/v1/items', None),
        ('GET', '/api/v1/providers/keys', None),
        ('GET', '/api/v1/planning/replenishment', None),
    ]
    for method, path, _body in available:
        resp = client.request(method, path, headers=_headers(token))
        assert resp.status_code in (200, 404), f'{path} failed: {resp.status_code}'


def test_free_cap_no_overage_path(client, signup_workspace, seed_csv_path, advance_usage):
    """NB-31.4: past the cap there is no partial-write allowance."""
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 3000)

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 423

    free_cap = _activation_free_cap(client, token)
    assert free_cap['locked'] is True
    assert free_cap['utilization_pct'] == 120
    assert free_cap['message'] is not None


def test_sample_and_real_data_lock_identically(client, signup_workspace, seed_csv_path):
    """NB-31.5: 50 sample-substrate optimizations hit the cap like real data."""
    _, token = signup_workspace()

    for _ in range(50):
        resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
        assert resp.status_code == 200, resp.text

    locked = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert locked.status_code == 423
    assert locked.json()['detail']['free_cap_locked'] is True


def test_lock_auto_lifts_at_month_rollover(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage
):
    """Decision #5: the window derives lazily from now — a moved window
    (new month) reads zero counters and the lock lifts with zero code."""
    from app.models.usage_meter import OrganizationUsageCounter

    org_id, token = signup_workspace()
    advance_usage(org_id, 'route_optimizations', 50)

    assert _activation_free_cap(client, token)['locked'] is True
    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 423

    # Simulate month rollover: move the counter row into the PREVIOUS
    # window; the current window now reads zero.
    today = datetime.now(UTC).date()
    current_start = today.replace(day=1)
    prev_start = (current_start - timedelta(days=1)).replace(day=1)
    prev_end = current_start - timedelta(days=1)
    counter = db_session.execute(
        select(OrganizationUsageCounter).where(
            OrganizationUsageCounter.organization_id == UUID(org_id),
            OrganizationUsageCounter.metric == 'route_optimizations',
        )
    ).scalar_one()
    counter.period_start = prev_start
    counter.period_end = prev_end
    db_session.commit()

    free_cap = _activation_free_cap(client, token)
    assert free_cap['locked'] is False
    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 200, resp.text


def test_phase_lock_and_free_cap_compose(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage
):
    """Decision #5: both locks held -> phase banner wins (still 423)."""
    org_id, token = signup_workspace()

    from app.models.collection_account import CollectionAccount

    cbe = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'cbe')
    ).scalar_one()
    today = datetime.now(UTC).date()
    invoice = SubscriptionInvoice(
        organization_id=UUID(org_id),
        invoice_number='INV-LOCK-1',
        tier='free',
        billing_period_start=today.replace(day=1),
        billing_period_end=today,
        flat_amount_etb=Decimal('0.00'),
        total_etb=Decimal('100.00'),
        balance_remaining_etb=Decimal('100.00'),
        due_date=today,
        grace_days=3,
        grace_ends_at=today + timedelta(days=1),
        designated_account_id=cbe.id,
        status='issued',
    )
    db_session.add(invoice)
    db_session.commit()

    advance_usage(org_id, 'delivery_tasks', 2500)

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 423
    detail = resp.json()['detail']
    assert detail['state'] == 'grace'
    assert detail['can_write'] is False
    assert 'free_cap_locked' not in detail


def test_select_tier_available_while_free_cap_locked(
    client, signup_workspace, seed_csv_path, advance_usage
):
    """NB-31.4 + decision #5: upgrade is the only way out — stays open."""
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 2500)

    resp = client.post(
        '/api/v1/subscriptions/select-tier', headers=_headers(token), json={'tier': 'starter'}
    )
    assert resp.status_code == 200, resp.text

    free_cap = _activation_free_cap(client, token)
    assert free_cap['locked'] is False

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 200, resp.text


def test_receipts_exempt_from_free_cap(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage, upload_receipt
):
    """Phase 2/3 cashflow carve-out: receipt servicing stays unguarded."""
    from decimal import Decimal as _Decimal

    from app.models.collection_account import CollectionAccount

    org_id, token = signup_workspace()

    # A free-tier org with an open invoice so receipt upload has a target.
    cbe = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'cbe')
    ).scalar_one()
    today = datetime.now(UTC).date()
    db_session.add(
        SubscriptionInvoice(
            organization_id=UUID(org_id),
            invoice_number='INV-CARVE-1',
            tier='free',
            billing_period_start=today.replace(day=1),
            billing_period_end=today,
            flat_amount_etb=_Decimal('0.00'),
            total_etb=_Decimal('4520.00'),
            balance_remaining_etb=_Decimal('4520.00'),
            due_date=today,
            grace_days=3,
            grace_ends_at=today + timedelta(days=1),
            designated_account_id=cbe.id,
            status='issued',
        )
    )
    db_session.commit()

    advance_usage(org_id, 'delivery_tasks', 2500)

    resp = upload_receipt(token)
    assert resp.status_code == 200, resp.text
    receipt_id = resp.json()['receipt_id']

    rows = client.get('/api/v1/receipts/queue', headers=_headers(token)).json()
    assert any(item['id'] == receipt_id for item in rows)

    decision = client.post(
        f'/api/v1/receipts/{receipt_id}/decision',
        headers=_headers(token),
        json={'verdict': 'reject_illegible', 'admin_note': 'unreadable'},
    )
    assert decision.status_code == 200, decision.text


def test_423_detail_contains_free_cap_fields(client, signup_workspace, seed_csv_path, advance_usage):
    org_id, token = signup_workspace()
    advance_usage(org_id, 'route_optimizations', 50)

    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 423
    detail = resp.json()['detail']
    assert detail['free_cap_locked'] is True
    assert detail['free_cap_message'] == (
        'Free tier cap reached. Writes resume next month, or upgrade now to continue immediately.'
    )
    assert detail['can_write'] is False
    assert detail['state'] == 'free_cap_locked'
