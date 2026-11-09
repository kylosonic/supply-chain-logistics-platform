"""NB-65: the feedback surface cannot be abused (audit H-5).

``POST /api/v1/feedback`` is authenticated-only: anonymous submissions are
rejected 401, signed-in users create rows, and the stored ``user_email`` is
the caller's identity unless the payload carries its own email. The schema
message cap stays enforced, and returning signed-in users are never blocked
Feedback must carry an authenticated identity.
"""
from __future__ import annotations

from sqlalchemy import select

from app.models.feedback import Feedback


def _feedback_payload(**overrides) -> dict:
    payload = {'category': 'bug', 'message': 'Console map pan is laggy'}
    payload.update(overrides)
    return payload


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def test_anonymous_feedback_rejected(client):
    resp = client.post('/api/v1/feedback', json=_feedback_payload())
    assert resp.status_code == 401
    assert 'authentication' in resp.json()['detail'].lower()


def test_authenticated_feedback_creates_row(client, admin_token, db_session):
    resp = client.post(
        '/api/v1/feedback', headers=_auth(admin_token), json=_feedback_payload()
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['category'] == 'bug'
    assert body['message'] == 'Console map pan is laggy'
    row = db_session.execute(select(Feedback)).scalars().one()
    assert row.category == 'bug'


def test_feedback_stamps_authenticated_user_email(client, admin_token, db_session):
    resp = client.post(
        '/api/v1/feedback', headers=_auth(admin_token), json=_feedback_payload()
    )
    assert resp.status_code == 200
    row = db_session.execute(select(Feedback)).scalars().one()
    assert row.user_email == 'admin@testco.com'


def test_feedback_preserves_provided_email(client, admin_token, db_session):
    resp = client.post(
        '/api/v1/feedback',
        headers=_auth(admin_token),
        json=_feedback_payload(user_email='external@example.com'),
    )
    assert resp.status_code == 200
    row = db_session.execute(select(Feedback)).scalars().one()
    assert row.user_email == 'external@example.com'


def test_feedback_message_validation_preserved(client, admin_token):
    resp = client.post(
        '/api/v1/feedback',
        headers=_auth(admin_token),
        json=_feedback_payload(message='x' * 2001),
    )
    assert resp.status_code == 422


def test_authenticated_repeat_submissions_allowed(client, admin_token, db_session):
    first = client.post(
        '/api/v1/feedback', headers=_auth(admin_token), json=_feedback_payload()
    )
    second = client.post(
        '/api/v1/feedback',
        headers=_auth(admin_token),
        json=_feedback_payload(category='feature'),
    )
    assert first.status_code == 200
    assert second.status_code == 200
    rows = db_session.execute(select(Feedback)).scalars().all()
    assert len(rows) == 2
