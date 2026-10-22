from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import OrganizationMembership
from app.models.user import User


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def test_workspace_admin_can_invite_and_accept_teammate(
    client: TestClient, admin_token: str, db_session: Session
):
    members = client.get('/api/v1/team/members', headers=_headers(admin_token))
    assert members.status_code == 200, members.text
    assert any(row['username'] == 'admin' for row in members.json())

    created = client.post(
        '/api/v1/team/invitations',
        headers=_headers(admin_token),
        json={'email': 'new.dispatcher@testco.com', 'role': 'operator'},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body['invite_url'].endswith(f'#token={body["token"]}')

    accepted = client.post(
        '/api/v1/team/invitations/accept',
        json={
            'token': body['token'],
            'username': 'dispatcher',
            'password': 'VeryStrongPass9',
            'full_name': 'New Dispatcher',
        },
    )
    assert accepted.status_code == 200, accepted.text
    token = accepted.json()['access_token']
    assert accepted.json()['organization_role'] == 'operator'

    me = client.get('/api/v1/auth/me', headers=_headers(token))
    assert me.status_code == 200
    assert me.json()['username'] == 'dispatcher'

    user = db_session.execute(select(User).where(User.username == 'dispatcher')).scalar_one()
    membership = db_session.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.is_active.is_(True),
        )
    ).scalar_one()
    assert membership.role == 'operator'


def test_viewer_cannot_invite_or_change_members(client: TestClient, viewer_token: str):
    denied = client.post(
        '/api/v1/team/invitations',
        headers=_headers(viewer_token),
        json={'email': 'blocked@testco.com', 'role': 'viewer'},
    )
    assert denied.status_code == 403
    assert client.get('/api/v1/team/members', headers=_headers(viewer_token)).status_code == 403


def test_invitation_can_be_revoked_and_cannot_be_reused(client: TestClient, admin_token: str):
    created = client.post(
        '/api/v1/team/invitations',
        headers=_headers(admin_token),
        json={'email': 'revoked@testco.com', 'role': 'viewer'},
    )
    assert created.status_code == 201, created.text
    body = created.json()

    revoke = client.delete(
        f'/api/v1/team/invitations/{body["invitation"]["id"]}',
        headers=_headers(admin_token),
    )
    assert revoke.status_code == 204, revoke.text

    accepted = client.post(
        '/api/v1/team/invitations/accept',
        json={
            'token': body['token'],
            'username': 'revoked_user',
            'password': 'VeryStrongPass9',
        },
    )
    assert accepted.status_code == 410


def test_member_role_can_change_but_owner_cannot_be_removed(client: TestClient, admin_token: str):
    members = client.get('/api/v1/team/members', headers=_headers(admin_token)).json()
    admin = next(row for row in members if row['username'] == 'admin')
    viewer = next(row for row in members if row['username'] == 'viewer')

    self_change = client.patch(
        f'/api/v1/team/members/{admin["membership_id"]}',
        headers=_headers(admin_token),
        json={'role': 'viewer'},
    )
    assert self_change.status_code == 409, self_change.text

    promoted = client.patch(
        f'/api/v1/team/members/{viewer["membership_id"]}',
        headers=_headers(admin_token),
        json={'role': 'operator'},
    )
    assert promoted.status_code == 200, promoted.text
    assert promoted.json()['role'] == 'operator'

    remove_owner = client.delete(
        f'/api/v1/team/members/{admin["membership_id"]}',
        headers=_headers(admin_token),
    )
    assert remove_owner.status_code == 409
