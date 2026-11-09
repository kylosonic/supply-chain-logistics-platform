from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection_account import CollectionAccount
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord


def _signup(client: TestClient, suffix: str, *, tier: str = 'starter') -> tuple[str, UUID]:
    resp = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': f'Billing Api Co {suffix}',
            'company_email': f'owner-{suffix}@billingapico.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': tier,
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


def _inject_invoice(db_session: Session, org_id: UUID, *, number: str, grace_ends_at: date) -> None:
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
            total_etb=4520,
            balance_remaining_etb=4520,
            due_date=period_start,
            grace_days=3,
            grace_ends_at=grace_ends_at,
            designated_account_id=account.id,
        )
    )
    db_session.commit()


def test_plan_catalog_etb_prices(client: TestClient):
    resp = client.get('/api/v1/subscriptions/plans')
    assert resp.status_code == 200
    plans = {plan['tier']: plan for plan in resp.json()}

    assert set(plans) == {'free', 'starter', 'scale', 'enterprise'}

    free = plans['free']
    assert free['flat_price_etb'] == '0.00'
    assert free['billing_cycle'] is None
    assert free['included_tasks_per_month'] == 2500
    assert free['overage_unit_price_etb'] is None

    starter = plans['starter']
    assert starter['flat_price_etb'] == '4500.00'
    assert starter['billing_cycle'] == 'monthly'
    assert starter['overage_unit_price_etb'] == '0.20'

    scale = plans['scale']
    assert scale['flat_price_etb'] == '10000.00'
    assert scale['billing_cycle'] == 'quarterly'
    assert scale['overage_unit_price_etb'] == '0.16'

    enterprise = plans['enterprise']
    assert enterprise['flat_price_etb'] == '45000.00'
    assert enterprise['billing_cycle'] == 'quarterly'
    assert enterprise['overage_unit_price_etb'] is None

    # USD fields preserved (existing contract).
    assert plans['starter']['monthly_price_usd'] == 399


def test_me_returns_billing_phase_and_trial(client: TestClient):
    token, _ = _signup(client, 'me')

    free_me = client.get('/api/v1/subscriptions/me', headers=_auth(token))
    assert free_me.status_code == 200
    assert free_me.json()['tier'] == 'free'
    assert free_me.json()['billing_phase'] == 'free'
    assert free_me.json()['trial_ends_at'] is None

    _upgrade(client, token)
    trial_me = client.get('/api/v1/subscriptions/me', headers=_auth(token))
    assert trial_me.status_code == 200
    body = trial_me.json()
    assert body['tier'] == 'starter'
    assert body['billing_phase'] == 'trial'
    assert body['status'] == 'trialing'
    assert body['trial_ends_at'] is not None
    assert body['next_billing_period_start'] is not None


def test_state_free_org_no_billing_surface(client: TestClient):
    token, _ = _signup(client, 'free')

    resp = client.get('/api/v1/billing/state', headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body['phase'] == 'free'
    assert body['can_write'] is True
    assert body['billing_visible'] is False
    assert body['banner_message'] is None
    assert body['due_date'] is None

    invoices = client.get('/api/v1/billing/invoices', headers=_auth(token))
    assert invoices.status_code == 200
    assert invoices.json() == []


def test_state_grace_banner(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'grace')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    # UTC-anchored so the day-difference assertion is stable on
    # machines whose local date (UTC+3) is ahead of the UTC date.
    _inject_invoice(
        db_session, org_id, number='INV-888001',
        grace_ends_at=datetime.now(UTC).date() + timedelta(days=1),
    )

    resp = client.get('/api/v1/billing/state', headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body['phase'] == 'grace'
    assert body['can_write'] is False
    assert body['billing_visible'] is True
    assert body['banner_message'] == 'Grace period: 1 days remaining'
    assert body['days_remaining'] == 1
    assert body['due_date'] is not None


def test_invoice_list_and_detail_include_designated_account(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'inv')
    _upgrade(client, token)
    _force_trial_ended(db_session, org_id)
    _inject_invoice(db_session, org_id, number='INV-888002', grace_ends_at=date.today() + timedelta(days=1))

    listing = client.get('/api/v1/billing/invoices', headers=_auth(token))
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    row = rows[0]
    assert row['invoice_number'] == 'INV-888002'
    assert row['total_etb'] == '4520.00'
    assert row['designated_account']['bank_code'] == 'cbe'
    assert row['designated_account']['bank_name']
    assert row['designated_account']['account_holder']
    assert row['designated_account']['account_number']
    assert row['status'] == 'issued'

    detail = client.get('/api/v1/billing/invoices/INV-888002', headers=_auth(token))
    assert detail.status_code == 200
    assert detail.json()['invoice_number'] == 'INV-888002'
    assert detail.json()['designated_account']['bank_code'] == 'cbe'

    missing = client.get('/api/v1/billing/invoices/INV-NOPE', headers=_auth(token))
    assert missing.status_code == 404


def test_notifications_list_and_dismiss_window(client: TestClient, db_session: Session):
    token, org_id = _signup(client, 'notif')
    _upgrade(client, token)

    db_session.add(
        Notification(
            organization_id=org_id,
            kind='invoice_warning',
            title='Invoice INV-900001 issued',
            message='Invoice INV-900001 for 4520.00 ETB is due on 2026-08-01.',
            payload={'invoice_number': 'INV-900001'},
            expires_at=datetime.now(UTC) + timedelta(days=2),
        )
    )
    db_session.commit()

    listing = client.get('/api/v1/notifications', headers=_auth(token))
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]['kind'] == 'invoice_warning'
    assert rows[0]['payload']['invoice_number'] == 'INV-900001'

    # Dismiss before expiry -> 409 (persists for the full 3-day window).
    early = client.post(f"/api/v1/notifications/{rows[0]['id']}/dismiss", headers=_auth(token))
    assert early.status_code == 409

    # Expire it, then dismiss -> 200.
    notification = db_session.get(Notification, rows[0]['id'])
    notification.expires_at = datetime.now(UTC) - timedelta(hours=1)
    db_session.commit()

    late = client.post(f"/api/v1/notifications/{rows[0]['id']}/dismiss", headers=_auth(token))
    assert late.status_code == 200
    assert late.json()['dismissed_at'] is not None
