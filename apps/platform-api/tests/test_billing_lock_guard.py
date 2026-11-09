from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection_account import CollectionAccount
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord


def _signup(client: TestClient, suffix: str) -> tuple[str, UUID]:
    resp = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': f'Lock Co {suffix}',
            'company_email': f'owner-{suffix}@lockco.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': 'starter',
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    return body['access_token'], UUID(body['organization']['id'])


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _upgrade(client: TestClient, token: str, tier: str = 'starter') -> dict:
    resp = client.post('/api/v1/subscriptions/select-tier', headers=_auth(token), json={'tier': tier})
    assert resp.status_code == 200
    return resp.json()


def _optimize_payload() -> dict:
    return {
        'route_name': 'Guard Test',
        'schedule_date': str(date.today()),
        'start_warehouse_code': 'WH-L1',
        'deliveries': [{'warehouse_code': 'WH-L2', 'demand_units': 25}],
        'vehicle_capacity_units': 250,
        'max_stops': 10,
        'speed_kmh': 45,
        'cost_per_km': 1.5,
        'persist_schedule': False,
    }


def _force_trial_ended(db_session: Session, org_id: UUID) -> None:
    """End the org's trial ~2h ago so the next billing period is in the future."""
    org = db_session.get(Organization, org_id)
    now = datetime.now(UTC)
    org.trial_started_at = now - timedelta(hours=170)
    org.trial_ends_at = now - timedelta(hours=2)
    trial = db_session.execute(
        select(TrialRecord).where(TrialRecord.organization_id == org_id)
    ).scalars().one()
    trial.started_at = now - timedelta(hours=170)
    trial.ended_at = now - timedelta(hours=2)
    db_session.commit()


def _inject_invoice(db_session: Session, org_id: UUID, *, grace_ends_at: date, number: str) -> None:
    account = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'cbe')
    ).scalar_one()
    today = date.today()
    period_start = today.replace(day=1)
    db_session.add(
        SubscriptionInvoice(
            organization_id=org_id,
            invoice_number=number,
            tier='starter',
            billing_period_start=period_start,
            billing_period_end=date(today.year, today.month, 28) + timedelta(days=4),
            flat_amount_etb=4500,
            total_etb=4500,
            balance_remaining_etb=4500,
            due_date=period_start,
            grace_days=3,
            grace_ends_at=grace_ends_at,
            designated_account_id=account.id,
        )
    )
    db_session.commit()


def test_write_blocked_in_limbo(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'limbo')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)

    resp = client.post('/api/v1/routes/optimize', headers=_auth(token), json=_optimize_payload())
    assert resp.status_code == 423
    detail = resp.json()['detail']
    assert detail['state'] == 'limbo'
    assert detail['can_write'] is False
    assert 'Your trial has ended. Your first invoice is due on' in detail['message']


def test_write_blocked_in_grace_with_days_remaining(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'grace')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(
        db_session, org_id,
        # UTC-anchored (see test_billing_api.py::test_state_grace_banner).
        grace_ends_at=datetime.now(UTC).date() + timedelta(days=1),
        number='INV-999001',
    )

    resp = client.post('/api/v1/routes/optimize', headers=_auth(token), json=_optimize_payload())
    assert resp.status_code == 423
    detail = resp.json()['detail']
    assert detail['state'] == 'grace'
    assert detail['can_write'] is False
    assert detail['days_remaining'] == 1
    assert detail['message'] == 'Grace period: 1 days remaining'


def test_write_blocked_in_hard_lock(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'hardlock')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(db_session, org_id, grace_ends_at=date.today() - timedelta(days=1), number='INV-999002')

    resp = client.post('/api/v1/routes/optimize', headers=_auth(token), json=_optimize_payload())
    assert resp.status_code == 423
    detail = resp.json()['detail']
    assert detail['state'] == 'hard_locked'
    assert detail['can_write'] is False


def test_reads_always_available(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'reads')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(db_session, org_id, grace_ends_at=date.today() - timedelta(days=1), number='INV-999003')

    resp = client.get('/api/v1/warehouses', headers=_auth(token))
    assert resp.status_code == 200
    me = client.get('/api/v1/subscriptions/me', headers=_auth(token))
    assert me.status_code == 200
    assert me.json()['billing_phase'] == 'hard_locked'


def test_auth_endpoints_exempt(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'authx')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(db_session, org_id, grace_ends_at=date.today() - timedelta(days=1), number='INV-999004')

    login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin12345'})
    assert login.status_code == 200


def test_select_tier_exempt_and_non_resetting(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'seltier')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(db_session, org_id, grace_ends_at=date.today() - timedelta(days=1), number='INV-999005')

    resp = client.post('/api/v1/subscriptions/select-tier', headers=_auth(token), json={'tier': 'scale'})
    assert resp.status_code == 200
    assert resp.json()['billing_phase'] == 'hard_locked'
    trials = db_session.execute(
        select(TrialRecord).where(TrialRecord.organization_id == org_id, TrialRecord.tier == 'scale')
    ).scalars().all()
    assert trials == []


def test_usage_record_guarded(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'usage')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(db_session, org_id, grace_ends_at=date.today() - timedelta(days=1), number='INV-999006')

    resp = client.post('/api/v1/subscriptions/usage/record', headers=_auth(token), json={'units': 5})
    assert resp.status_code == 423
    assert resp.json()['detail']['state'] == 'hard_locked'


def test_no_membership_cannot_write(client: TestClient, db_session: Session, orgless_token: str):
    payload = {
        'code': 'WH-PT',
        'name': 'Passthrough WH',
        'address': 'Addr',
        'city': 'City',
        'state': 'State',
        'country': 'ET',
        'latitude': 8.98,
        'longitude': 38.75,
        'capacity_units': 1000,
    }
    resp = client.post('/api/v1/warehouses', json=payload, headers=_auth(orgless_token))
    assert resp.status_code == 403


def test_trial_and_free_phases_unaffected(client: TestClient, db_session: Session):
    # Free phase: writable.
    free_token, _ = _signup(client, 'freewrite')
    warehouse_resp = client.post(
        '/api/v1/warehouses',
        headers=_auth(free_token),
        json={
            'code': 'WH-FR',
            'name': 'Free WH',
            'address': 'Addr',
            'city': 'City',
            'state': 'State',
            'country': 'ET',
            'latitude': 8.97,
            'longitude': 38.74,
            'capacity_units': 900,
        },
    )
    assert warehouse_resp.status_code == 201

    # Trial phase: full write access (routes/optimize 200).
    trial_token, _ = _signup(client, 'trialwrite')
    _upgrade(client, trial_token)
    resp = client.post(
        '/api/v1/routes/optimize',
        headers=_auth(trial_token),
        json={
            **_optimize_payload(),
            'start_warehouse_code': 'WH-001',
            'deliveries': [{'warehouse_code': 'WH-002', 'demand_units': 25}],
        },
    )
    assert resp.status_code == 200
