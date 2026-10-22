"""Phase 4 milestone-6 toast tests (blueprint §10.2 — test_activation_toast.py, NB-33).

Soft post-aha toast: fires exactly once per organization on the first
route optimization run, any substrate, informational only (no CTA),
auto-dismiss is a console concern (6s timer in PostAhaToast).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activation_state import OrganizationActivationState
from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.schemas.route import RouteOptimizeResponse

_OPTIMIZE = {
    'route_name': 'Toast Route',
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


def test_toast_fires_once_per_organization(client, db_session: Session, signup_workspace, seed_csv_path):
    """NB-33.4: first optimize -> post_aha_toast true + toast_fired_at set;
    second optimize -> false (server truth)."""
    org_id, token = signup_workspace()

    first = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert first.status_code == 200, first.text
    assert first.json()['post_aha_toast'] is True

    state = db_session.execute(
        select(OrganizationActivationState).where(
            OrganizationActivationState.organization_id == UUID(org_id)
        )
    ).scalar_one()
    assert state.m6_completed_at is not None
    assert state.toast_fired_at is not None

    second = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert second.status_code == 200, second.text
    assert second.json()['post_aha_toast'] is False

    milestones = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'activation.milestone_6_completed')
    ).scalars().all()
    assert len(milestones) == 1


def test_toast_fires_on_sample_data(client, signup_workspace, seed_csv_path):
    """NB-33.5: full-sample substrate still fires the toast."""
    _, token = signup_workspace()
    resp = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert resp.status_code == 200, resp.text
    assert resp.json()['post_aha_toast'] is True
    assert resp.json()['data_origin'] == 'sample'


def test_toast_no_cta_fields():
    """NB-33.2: the response schema carries no upgrade/price/CTA fields."""
    fields = set(RouteOptimizeResponse.model_fields.keys())
    assert 'post_aha_toast' in fields
    assert 'data_origin' in fields
    for banned in ('upgrade_url', 'pricing_url', 'cta', 'price', 'upgrade'):
        assert banned not in fields


def test_toast_survives_second_user(
    client, db_session: Session, signup_workspace, seed_csv_path
):
    """NB-33.4: a second user's first optimization does not re-fire."""
    org_id, token = signup_workspace()

    first = client.post('/api/v1/routes/optimize', headers=_headers(token), json=_OPTIMIZE)
    assert first.json()['post_aha_toast'] is True

    operator = db_session.execute(
        select(User).where(User.username == 'operator')
    ).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=UUID(org_id), user_id=operator.id, role='operator', is_active=True
        )
    )
    db_session.commit()

    resp = client.post('/api/v1/auth/login', json={'username': 'operator', 'password': 'operator12345'})
    assert resp.status_code == 200
    operator_token = resp.json()['access_token']

    second = client.post(
        '/api/v1/routes/optimize',
        headers={**_headers(operator_token), 'X-Organization-Id': org_id},
        json=_OPTIMIZE,
    )
    assert second.status_code == 200, second.text
    assert second.json()['post_aha_toast'] is False
