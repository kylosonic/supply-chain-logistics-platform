from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


def test_register_login_and_me_flow(client: TestClient, admin_token: str):
    register = client.post(
        '/api/v1/auth/register',
        json={'username': 'new_user', 'password': 'SomeStrongPass9', 'role': 'viewer'},
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert register.status_code == 201
    assert register.json()['username'] == 'new_user'

    login = client.post('/api/v1/auth/login', json={'username': 'new_user', 'password': 'SomeStrongPass9'})
    assert login.status_code == 200
    token = login.json()['access_token']

    me = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    assert me.json()['username'] == 'new_user'


def test_admin_only_users_endpoint_forbidden_for_viewer(client: TestClient, viewer_token: str):
    resp = client.get('/api/v1/auth/users', headers={'Authorization': f'Bearer {viewer_token}'})
    assert resp.status_code == 403


def test_admin_only_users_endpoint_ok_for_admin(client: TestClient, admin_token: str):
    resp = client.get('/api/v1/auth/users', headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 200
    payload = resp.json()
    assert any(user['username'] == 'admin' for user in payload)


def test_logout_revokes_the_presented_access_token(client: TestClient, admin_token: str):
    headers = {'Authorization': f'Bearer {admin_token}'}
    assert client.get('/api/v1/auth/me', headers=headers).status_code == 200

    logout = client.post('/api/v1/auth/logout', headers=headers)
    assert logout.status_code == 200, logout.text
    assert client.get('/api/v1/auth/me', headers=headers).status_code == 401

    login = client.post(
        '/api/v1/auth/login',
        json={'username': 'admin', 'password': 'admin12345'},
    )
    assert login.status_code == 200
    fresh = {'Authorization': f"Bearer {login.json()['access_token']}"}
    assert client.get('/api/v1/auth/me', headers=fresh).status_code == 200


def test_register_requires_admin_when_users_exist(client: TestClient):
    resp = client.post(
        '/api/v1/auth/register',
        json={'username': 'no_auth_register', 'password': 'SomeStrongPass9', 'role': 'viewer'},
    )
    assert resp.status_code == 401


def test_first_registration_without_auth_bootstraps_admin():
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    session: Session = TestingSessionLocal()

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            resp = client.post(
                '/api/v1/auth/register',
                json={'username': 'first_admin', 'password': 'SomeStrongPass9', 'role': 'viewer'},
            )
            assert resp.status_code == 201
            payload = resp.json()
            assert payload['username'] == 'first_admin'
            assert payload['role'] == 'admin'
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=engine)
