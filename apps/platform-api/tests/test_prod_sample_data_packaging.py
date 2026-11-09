"""PROD-01 packaging tests — sample-data baked into the API image.

(a) Static packaging tests pinning the regression that shipped: the
    Dockerfile copied ``app``/``alembic``/``scripts`` but NOT ``sample-data``,
    so signup-time seeding crashed in the container (settings.sample_data_dir
    could not resolve, and the repo-root walk-up is a dev-only convenience).
(b) Behavioral hermetic tests proving the runtime path resolves purely from
    ``settings.sample_data_dir``: a pristine CWD outside the repo must be able
    to seed (container-like), and must NOT be rescued by any repo walk-up.

Adjudication #1: both strategies are load-bearing. Never import app.api.
"""
from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.organization import Organization
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.activation.seeding import seed_workspace

PLATFORM_API_DIR = Path(__file__).resolve().parents[1]
BUILD_CONTEXT_SAMPLE_DIR = PLATFORM_API_DIR / 'sample-data'
DOCKERFILE_PATH = PLATFORM_API_DIR / 'Dockerfile'

# Phase-4 header contract (decision #11) — load-bearing, must never regress.
CSV_HEADER_CONTRACT = {
    'warehouses.csv': 'code,name,address,city,state,country,latitude,longitude,capacity_units',
    'items.csv': 'sku,name,category,unit_cost,reorder_level,temperature_threshold',
    'fleet_assets.csv': 'vehicle_code,driver_name,driver_contact,capacity_units,status',
    'inventory.csv': 'warehouse_code,sku,quantity_on_hand,safety_stock',
    'orders.csv': (
        'order_date,warehouse_code,sku,quantity,unit_price,customer_region,'
        'weather_avg_temp_c,weather_precip_mm,weather_disruption_index'
    ),
}

CSV_NAMES = sorted(CSV_HEADER_CONTRACT)


def _fresh_org(db: Session) -> Organization:
    org = Organization(
        name='Packaging Co',
        slug='packaging-co',
        primary_email_domain='packagingco.com',
        subscription_tier='free',
        subscription_status='active',
        billing_phase='free',
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _admin_user(db: Session) -> User:
    return db.execute(select(User).where(User.username == 'admin')).scalar_one()


def test_dockerfile_builder_stage_copies_sample_data():
    """The builder stage must COPY the CSVs into the build image."""
    text = DOCKERFILE_PATH.read_text()
    assert 'COPY sample-data ./sample-data' in text


def test_dockerfile_runtime_stage_copies_sample_data():
    """The runtime stage must inherit the CSVs from the builder."""
    text = DOCKERFILE_PATH.read_text()
    assert 'COPY --from=builder /app/sample-data ./sample-data' in text


def test_build_context_contains_all_five_sample_csvs():
    """All 5 CSVs must live in the build context (apps/platform-api/) with
    the phase-4 header contract intact (headers are load-bearing)."""
    assert BUILD_CONTEXT_SAMPLE_DIR.is_dir()
    present = {p.name for p in BUILD_CONTEXT_SAMPLE_DIR.glob('*.csv')}
    assert present == set(CSV_NAMES)
    for name in CSV_NAMES:
        header = (BUILD_CONTEXT_SAMPLE_DIR / name).read_text().splitlines()[0].strip()
        assert header == CSV_HEADER_CONTRACT[name], f'{name} header contract broken'


def test_seed_resolves_from_settings_dir_in_pristine_cwd(
    db_session: Session, tmp_path, monkeypatch
):
    """Container-like proof: from an empty CWD outside the repo, seeding must
    resolve purely via ``settings.sample_data_dir`` (absolute temp copy of the
    shipped CSVs) — rows per category > 0 and the audit event fires."""
    monkeypatch.chdir(tmp_path)

    sample_copy = tmp_path / 'sample-data'
    shutil.copytree(BUILD_CONTEXT_SAMPLE_DIR, sample_copy)
    monkeypatch.setattr(settings, 'sample_data_dir', str(sample_copy))

    org = _fresh_org(db_session)
    result = seed_workspace(
        db_session, org, _admin_user(db_session), now=datetime.now(UTC)
    )
    db_session.commit()  # seed_workspace is commit-aware; the caller commits
    rows = result['rows_per_category']
    assert rows['warehouses'] > 0
    assert rows['items'] > 0
    assert rows['fleet_assets'] > 0
    assert rows['inventory'] > 0
    assert rows['orders'] > 0

    event = db_session.execute(
        select(AuditEvent).where(AuditEvent.event_type == 'workspace.seeded_sample_data')
    ).scalars().first()
    assert event is not None
    assert event.organization_id == org.id
    assert event.payload['rows_per_category'] == rows

    # sanity: rows really were created through the settings-only path
    assert db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == org.id)
    ).scalars().all()


def test_seed_raises_when_sample_dir_unresolvable(db_session: Session, tmp_path, monkeypatch):
    """Negative control: a container-like CWD with no sample-data anywhere
    must raise — the repo-root walk-up must NOT rescue production."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, 'sample_data_dir', 'sample-data')

    org = _fresh_org(db_session)
    with pytest.raises(FileNotFoundError):
        seed_workspace(db_session, org, _admin_user(db_session), now=datetime.now(UTC))
