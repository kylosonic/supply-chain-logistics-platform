"""Phase 4 upgrade-pitch tests (blueprint §10.2 — test_upgrade_pitch.py, NB-32).

60/80/100 ladder: fire-once-per-threshold-per-month crossings, p60
dismissible, p80 persistent, p100 = the free-cap lock state itself
(decision #6). Utilization = max(pct_delivery_tasks, pct_route_optimizations).
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.threshold_crossing import ThresholdCrossing


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _activation_pitch(client, token: str) -> dict:
    resp = client.get('/api/v1/activation', headers=_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()['pitch']


def _prev_window_start() -> tuple:
    today = datetime.now(UTC).date()
    current_start = today.replace(day=1)
    prev_start = (current_start - timedelta(days=1)).replace(day=1)
    return prev_start, current_start - timedelta(days=1)


def test_p60_fires_at_sixty_percent_once_per_month(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage
):
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 1500)  # 60% of 2500

    pitch = _activation_pitch(client, token)
    assert pitch['banner'] == 'p60'
    assert pitch['dismissible'] is True
    assert pitch['fired'] == ['p60']

    audit = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'usage.pitch_fired')
    ).scalars().first()
    assert audit is not None
    assert audit.payload['level'] == 'p60'
    assert audit.payload['utilization_pct'] == 60

    # second read: no re-fire (NB-32.5)
    pitch = _activation_pitch(client, token)
    assert pitch['banner'] == 'p60'
    assert pitch['fired'] == []

    crossings = db_session.execute(
        select(ThresholdCrossing).where(ThresholdCrossing.organization_id == UUID(org_id))
    ).scalars().all()
    assert len(crossings) == 1
    assert crossings[0].threshold_level == 'p60'


def test_p60_dismissible_and_returns_next_month(
    client, db_session: Session, signup_workspace, seed_csv_path, advance_usage
):
    from app.models.usage_meter import OrganizationUsageCounter

    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 1500)
    assert _activation_pitch(client, token)['banner'] == 'p60'

    resp = client.post(
        '/api/v1/activation/pitch-dismiss', headers=_headers(token), json={'level': 'p60'}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {'dismissed': True}

    pitch = _activation_pitch(client, token)
    assert pitch['banner'] is None

    # Simulate a new month: move crossing + counter to the previous window
    # and re-advance usage in the current window -> fresh crossing fires.
    prev_start, prev_end = _prev_window_start()
    for model, _origin in (
        (ThresholdCrossing, 'sample'),
        (OrganizationUsageCounter, 'sample'),
    ):
        row = db_session.execute(
            select(model).where(model.organization_id == UUID(org_id))
        ).scalars().first()
        if row is not None:
            row.period_start = prev_start
            if hasattr(row, 'period_end'):
                row.period_end = prev_end
            db_session.add(row)
    db_session.commit()

    advance_usage(org_id, 'delivery_tasks', 1500)
    pitch = _activation_pitch(client, token)
    assert pitch['banner'] == 'p60'
    assert pitch['fired'] == ['p60']


def test_p80_fires_and_not_dismissible(client, signup_workspace, seed_csv_path, advance_usage):
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 2000)  # 80% of 2500

    pitch = _activation_pitch(client, token)
    assert pitch['banner'] == 'p80'
    assert pitch['dismissible'] is False
    assert 'p60' in pitch['fired']
    assert 'p80' in pitch['fired']

    resp = client.post(
        '/api/v1/activation/pitch-dismiss', headers=_headers(token), json={'level': 'p80'}
    )
    assert resp.status_code == 422

    pitch = _activation_pitch(client, token)
    assert pitch['banner'] == 'p80'


def test_p100_supersedes_p80(client, signup_workspace, seed_csv_path, advance_usage):
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 2000)
    assert _activation_pitch(client, token)['banner'] == 'p80'

    advance_usage(org_id, 'delivery_tasks', 500)  # 2500 -> locked
    pitch = _activation_pitch(client, token)
    assert pitch['banner'] == 'p100'
    assert pitch['dismissible'] is False


def test_banner_stack_order(client, signup_workspace, seed_csv_path, advance_usage):
    """p100 > p80 > p60 across three independent orgs."""
    org60, token60 = signup_workspace(name='Stack Co 60')
    org80, token80 = signup_workspace(name='Stack Co 80')
    org100, token100 = signup_workspace(name='Stack Co 100')

    advance_usage(org60, 'delivery_tasks', 1500)
    advance_usage(org80, 'delivery_tasks', 2000)
    advance_usage(org100, 'delivery_tasks', 2500)

    assert _activation_pitch(client, token60)['banner'] == 'p60'
    assert _activation_pitch(client, token80)['banner'] == 'p80'
    assert _activation_pitch(client, token100)['banner'] == 'p100'


def test_pitch_cta_targets_in_product_account(client, signup_workspace, seed_csv_path, advance_usage):
    """The pitch payload carries no CTA — the console renders /account links
    (NB-32.4: never leaves the console); server asserts payload shape only."""
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 2000)

    pitch = _activation_pitch(client, token)
    assert set(pitch.keys()) == {'banner', 'dismissible', 'fired'}
    assert pitch['banner'] == 'p80'


def test_crossings_cleared_on_upgrade_never_needed(
    client, signup_workspace, seed_csv_path, advance_usage
):
    """Non-free tier -> pitch payload is null (no crossings evaluated)."""
    org_id, token = signup_workspace()
    advance_usage(org_id, 'delivery_tasks', 2000)
    assert _activation_pitch(client, token)['banner'] == 'p80'

    resp = client.post(
        '/api/v1/subscriptions/select-tier', headers=_headers(token), json={'tier': 'starter'}
    )
    assert resp.status_code == 200, resp.text

    pitch = _activation_pitch(client, token)
    assert pitch == {'banner': None, 'dismissible': False, 'fired': []}
