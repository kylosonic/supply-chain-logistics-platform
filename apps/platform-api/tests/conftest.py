from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.collection_account import CollectionAccount
from app.models.user import User
from app.schemas.auth import UserRole
from app.services.security import hash_password


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    admin = User(
        username='admin',
        email='admin@testco.com',
        full_name='Admin User',
        password_hash=hash_password('admin12345'),
        role=UserRole.ADMIN,
        is_active=True,
    )
    viewer = User(
        username='viewer',
        email='viewer@testco.com',
        full_name='Viewer User',
        password_hash=hash_password('viewer12345'),
        role=UserRole.VIEWER,
        is_active=True,
    )
    operator = User(
        username='operator',
        email='operator@testco.com',
        full_name='Operator User',
        password_hash=hash_password('operator12345'),
        role=UserRole.OPERATOR,
        is_active=True,
    )
    session.add_all([admin, viewer, operator])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def seed_collection_accounts(db_session: Session) -> Generator[None, None, None]:
    """Seed the two collection accounts (CBE + Dashen) for every test."""
    db_session.add_all(
        [
            CollectionAccount(
                bank_code='cbe',
                bank_name='Commercial Bank of Ethiopia',
                account_holder='FreightPilot PLC',
                account_number='1000134567890',
                is_active=True,
            ),
            CollectionAccount(
                bank_code='dashen',
                bank_name='Dashen Bank S.C.',
                account_holder='FreightPilot PLC',
                account_number='012345678901',
                is_active=True,
            ),
        ]
    )
    db_session.commit()
    yield


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
