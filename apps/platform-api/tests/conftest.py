from __future__ import annotations

import json
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.collection_account import CollectionAccount
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord
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


# ---------------------------------------------------------------------------
# Phase 2 receipt-processing fixtures (blueprint §9.1)
#
# The signup/upgrade/force-trial-ended/inject-invoice recipe below is a
# deliberate REPLICATION of the file-local helpers in test_billing_api.py
# (never imported across test modules — test isolation; blueprint §11.11).
# ---------------------------------------------------------------------------

SAMPLE_PNG_BYTES = b'\x89PNG\r\n\x1a\n' + bytes(range(256)) * 4
BAD_FORMAT_BYTES = b'this is a plain text file pretending to be a receipt'
MINIMAL_PDF_BYTES = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n'


def sample_receipt_bytes() -> bytes:
    return SAMPLE_PNG_BYTES


def bad_format_bytes() -> bytes:
    return BAD_FORMAT_BYTES


def pdf_bytes() -> bytes:
    return MINIMAL_PDF_BYTES


def mock_extraction_payload(**overrides) -> dict:
    """Canonical 8-field extraction dict for mock-mode tests."""
    payload = {
        'fields': {
            'sender_name': 'Mulugeta Tesfaye',
            'sender_account_number': '1000123456',
            'receiver_account_number': '1000134567890',
            'receiver_name': 'FreightPilot PLC',
            'transfer_amount': '4520.00',
            'transfer_date': '2026-08-01',
            'reference_number': 'TXN-1001',
            'bank_identifier': 'cbe',
        },
        'confidence': {name: 0.95 for name in ('sender_name', 'sender_account_number', 'receiver_account_number', 'receiver_name', 'transfer_amount', 'transfer_date', 'reference_number', 'bank_identifier')},
        'model_name': 'mock-1',
    }
    payload.update(overrides)
    return payload


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture()
def make_paid_org_with_open_invoice(client: TestClient, db_session: Session):
    """Replicated Phase 1 recipe -> (org, invoice, token).

    Creates a paid-tier org whose trial ended and injects an open invoice
    with the requested balance (default 4520.00 ETB, grace in the future).
    """

    def _make(
        *,
        tier: str = 'starter',
        balance_etb: Decimal | int = Decimal('4520.00'),
        invoice_number: str = 'INV-000100',
        period_start: date | None = None,
        with_ai_key: bool = True,
    ) -> tuple[Organization, SubscriptionInvoice, str]:
        resp = client.post(
            '/api/v1/auth/company-signup',
            json={
                'company_name': f'Receipt Co {invoice_number}',
                'company_email': f'owner-{invoice_number.lower()}@receiptco.com',
                'password': 'VeryStrongPass9',
                'full_name': 'Owner User',
                'subscription_tier': tier,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        token = body['access_token']
        org_id = UUID(body['organization']['id'])

        up = client.post('/api/v1/subscriptions/select-tier', headers=_auth(token), json={'tier': tier})
        assert up.status_code == 200

        org = db_session.get(Organization, org_id)
        now = datetime.now(UTC)
        org.trial_started_at = now - timedelta(hours=170)
        org.trial_ends_at = now - timedelta(hours=2)
        trial = db_session.execute(
            select(TrialRecord).where(TrialRecord.organization_id == org_id)
        ).scalars().one()
        trial.started_at = now - timedelta(hours=170)
        trial.ended_at = now - timedelta(hours=2)
        if with_ai_key:
            from app.models.provider_key import ProviderApiKey
            from app.models.user import User as _User
            from app.services.security import encrypt_provider_key, mask_provider_key

            owner = db_session.execute(
                select(_User).where(_User.email == f'owner-{invoice_number.lower()}@receiptco.com')
            ).scalar_one()
            key = ProviderApiKey(
                organization_id=org_id,
                created_by_user_id=owner.id,
                provider_name='mock',
                key_name='primary',
                masked_key=mask_provider_key('sk-mock-1234567890'),
                encrypted_key=encrypt_provider_key('sk-mock-1234567890'),
                status='active',
            )
            db_session.add(key)
            db_session.flush()
            org.preferred_ai_provider = 'mock'
            org.preferred_ai_key_id = key.id
        db_session.commit()

        account = db_session.execute(
            select(CollectionAccount).where(CollectionAccount.bank_code == 'cbe')
        ).scalar_one()
        today = date.today()
        start = period_start or today.replace(day=1)
        invoice = SubscriptionInvoice(
            organization_id=org_id,
            invoice_number=invoice_number,
            tier=tier,
            billing_period_start=start,
            billing_period_end=date(today.year, today.month, 28) + timedelta(days=4),
            flat_amount_etb=Decimal('4500.00'),
            total_etb=Decimal('4520.00'),
            balance_remaining_etb=Decimal(balance_etb),
            due_date=start,
            grace_days=3,
            grace_ends_at=date.today() + timedelta(days=1),
            designated_account_id=account.id,
            status='issued',
        )
        db_session.add(invoice)
        db_session.commit()
        db_session.refresh(invoice)
        return org, invoice, token

    return _make


@pytest.fixture()
def upload_receipt(client: TestClient):
    """Multipart upload helper against POST /api/v1/receipts/upload."""

    def _upload(
        token: str,
        *,
        filename: str = 'receipt.png',
        content: bytes | None = None,
        content_type: str | None = None,
        mock_extraction: dict | None = None,
        mock_json: str | None = None,
    ):
        files = {'file': (filename, content or SAMPLE_PNG_BYTES, content_type or 'image/png')}
        data = {}
        if mock_json is not None:
            data['mock_extraction'] = mock_json
        elif mock_extraction is not None:
            data['mock_extraction'] = json.dumps(mock_extraction)
        return client.post('/api/v1/receipts/upload', headers=_auth(token), files=files, data=data)

    return _upload


@pytest.fixture()
def make_admin_membership(db_session: Session):
    """Owner-role membership for the conftest admin user (admin queue tests)."""

    def _make(org: Organization) -> OrganizationMembership:
        admin = db_session.execute(
            select(User).where(User.username == 'admin')
        ).scalar_one()
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=admin.id,
            role='owner',
            is_active=True,
        )
        db_session.add(membership)
        db_session.commit()
        db_session.refresh(membership)
        return membership

    return _make
