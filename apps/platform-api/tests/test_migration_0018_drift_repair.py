"""Migration 0018 (schema drift repair) tests — model of the 0017 harness.

Proves the revision closes the model-vs-migration drift on old-shape schemas:
route_schedules without assigned_asset_id/origin_latitude/origin_longitude,
alerts without payload, shipments without scope_3_emissions_kg.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.pool import StaticPool

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'alembic' / 'versions'
_MODULE_PATH = _MIGRATIONS_DIR / '20260808_0018_schema_drift_repair.py'


def _load_module():
    spec = importlib.util.spec_from_file_location('migration_0018', _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_engine():
    return sa.create_engine(
        'sqlite+pysqlite:///:memory:',
        poolclass=StaticPool,
    )


def _old_shape_engine():
    """Schema as migrations 0001..0017 leave it (pre-0018 drift shape)."""
    engine = _make_engine()
    with engine.begin() as conn:
        conn.execute(sa.text(
            'CREATE TABLE fleet_assets (id CHAR(32) PRIMARY KEY)'
        ))
        conn.execute(sa.text(
            'CREATE TABLE route_schedules (id CHAR(32) PRIMARY KEY, route_name VARCHAR, '
            'schedule_date DATE, start_warehouse_id CHAR(32), vehicle_capacity_units INTEGER, '
            'objective VARCHAR, total_distance_km FLOAT, total_cost FLOAT, '
            'estimated_duration_min INTEGER, status VARCHAR)'
        ))
        conn.execute(sa.text(
            'CREATE TABLE alerts (id CHAR(32) PRIMARY KEY, kind VARCHAR, severity VARCHAR, '
            'title VARCHAR, message VARCHAR)'
        ))
        conn.execute(sa.text(
            'CREATE TABLE shipments (id CHAR(32) PRIMARY KEY, shipment_no VARCHAR, '
            'total_distance_km FLOAT)'
        ))
    return engine


def _run_upgrade(engine, module):
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()


def _run_downgrade(engine, module):
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.downgrade()


@pytest.fixture()
def module():
    return _load_module()


def test_0018_upgrade_adds_all_missing_columns(module):
    engine = _old_shape_engine()
    _run_upgrade(engine, module)
    inspector = sa.inspect(engine)

    route_cols = {c['name'] for c in inspector.get_columns('route_schedules')}
    assert {'assigned_asset_id', 'origin_latitude', 'origin_longitude'} <= route_cols

    alert_cols = {c['name'] for c in inspector.get_columns('alerts')}
    assert 'payload' in alert_cols

    shipment_cols = {c['name'] for c in inspector.get_columns('shipments')}
    assert 'scope_3_emissions_kg' in shipment_cols

    # NOT NULL + server_default on shipments must make bare inserts work.
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO shipments (id, shipment_no) VALUES ('x', 'S-1')"
        ))
        scope3 = conn.execute(sa.text(
            "SELECT scope_3_emissions_kg FROM shipments WHERE id = 'x'"
        )).scalar()
        assert scope3 == 0


def test_0018_upgrade_is_idempotent(module):
    engine = _old_shape_engine()
    _run_upgrade(engine, module)
    _run_upgrade(engine, module)  # second pass must be a no-op
    inspector = sa.inspect(engine)
    route_cols = {c['name'] for c in inspector.get_columns('route_schedules')}
    assert 'assigned_asset_id' in route_cols


def test_0018_downgrade_is_noop_and_preserves_columns(module):
    engine = _old_shape_engine()
    _run_upgrade(engine, module)
    _run_downgrade(engine, module)
    inspector = sa.inspect(engine)
    route_cols = {c['name'] for c in inspector.get_columns('route_schedules')}
    assert 'assigned_asset_id' in route_cols
    assert 'origin_latitude' in route_cols
