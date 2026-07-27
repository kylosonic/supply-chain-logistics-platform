from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.auth import UserRole
from app.services.security import hash_password


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    admin = User(username='admin', password_hash=hash_password('admin12345'), role=UserRole.ADMIN, is_active=True)
    viewer = User(username='viewer', password_hash=hash_password('viewer12345'), role=UserRole.VIEWER, is_active=True)
    operator = User(username='operator', password_hash=hash_password('operator12345'), role=UserRole.OPERATOR, is_active=True)
    session.add_all([admin, viewer, operator])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    resp = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin12345'})
    assert resp.status_code == 200
    return resp.json()['access_token']


@pytest.fixture()
def viewer_token(client: TestClient) -> str:
    resp = client.post('/api/v1/auth/login', json={'username': 'viewer', 'password': 'viewer12345'})
    assert resp.status_code == 200
    return resp.json()['access_token']


@pytest.fixture()
def operator_token(client: TestClient) -> str:
    resp = client.post('/api/v1/auth/login', json={'username': 'operator', 'password': 'operator12345'})
    assert resp.status_code == 200
    return resp.json()['access_token']
