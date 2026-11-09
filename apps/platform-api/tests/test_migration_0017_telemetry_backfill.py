"""TDD regression tests for 20260806_0017_fleet_asset_telemetry_backfill.

The historical 0005 migration originally created ``fleet_assets`` without the
telemetry columns; 0017 is the idempotent forward repair. These tests run the
migration module against a throwaway sqlite in-memory schema (blueprint §2a).
"""
from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'alembic' / 'versions'
_MIGRATION_0017 = _MIGRATIONS_DIR / '20260806_0017_fleet_asset_telemetry_backfill.py'


def _load_0017_module():
    spec = importlib.util.spec_from_file_location('test_0017_telemetry_backfill_mod', _MIGRATION_0017)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_engine() -> Engine:
    return sa.create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )


def _create_fleet_assets_old_0005_shape(conn) -> None:
    """The original (pre-repair) 0005 shape: no telemetry columns."""
    conn.execute(
        sa.text(
            'CREATE TABLE fleet_assets ('
            'vehicle_code VARCHAR(64) NOT NULL, '
            'driver_name VARCHAR(128) NOT NULL, '
            'driver_contact VARCHAR(128), '
            'capacity_units INTEGER NOT NULL, '
            'status VARCHAR(24) NOT NULL, '
            'id VARCHAR NOT NULL, '
            'created_at DATETIME NOT NULL, '
            'PRIMARY KEY (id)'
            ')'
        )
    )


def _create_fleet_assets_fixed_shape(conn) -> None:
    _create_fleet_assets_old_0005_shape(conn)
    conn.execute(sa.text('ALTER TABLE fleet_assets ADD COLUMN latitude FLOAT'))
    conn.execute(sa.text('ALTER TABLE fleet_assets ADD COLUMN longitude FLOAT'))
    conn.execute(sa.text('ALTER TABLE fleet_assets ADD COLUMN last_telemetry_at DATETIME'))


def test_0017_upgrade_adds_telemetry_columns_when_missing():
    module = _load_0017_module()
    engine = _make_engine()
    with engine.connect() as conn:
        _create_fleet_assets_old_0005_shape(conn)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()

        columns = {col['name'] for col in sa.inspect(conn).get_columns('fleet_assets')}
        assert {'latitude', 'longitude', 'last_telemetry_at'} <= columns

        # Float / DateTime round-trip on the added columns.
        inserted = datetime(2026, 8, 6, 12, 30, 0)
        conn.execute(
            sa.text(
                'INSERT INTO fleet_assets '
                '(id, vehicle_code, driver_name, capacity_units, status, '
                'latitude, longitude, last_telemetry_at, created_at) '
                'VALUES (:id, :vc, :dn, :cap, :st, :lat, :lon, :lta, :crt)'
            ),
            {
                'id': 'asset-1',
                'vc': 'TRK-001',
                'dn': 'Driver One',
                'cap': 10,
                'st': 'active',
                'lat': 9.0244,
                'lon': 38.7469,
                'lta': inserted,
                'crt': inserted,
            },
        )
        row = conn.execute(sa.text('SELECT latitude, longitude, last_telemetry_at FROM fleet_assets')).one()
        assert row.latitude == 9.0244
        assert row.longitude == 38.7469
        # sqlite3 has no default datetime converter on the fetch side, so a raw
        # text() SELECT returns an ISO string; parse it back for the round-trip.
        assert datetime.fromisoformat(str(row.last_telemetry_at)) == inserted


def test_0017_upgrade_is_idempotent_on_existing_columns():
    module = _load_0017_module()
    engine = _make_engine()
    with engine.connect() as conn:
        _create_fleet_assets_fixed_shape(conn)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
        with Operations.context(ctx):
            module.upgrade()  # second run must not raise duplicate-column errors

        columns = {col['name'] for col in sa.inspect(conn).get_columns('fleet_assets')}
        assert {'latitude', 'longitude', 'last_telemetry_at'} <= columns


def test_0017_downgrade_is_noop_and_preserves_columns():
    module = _load_0017_module()
    engine = _make_engine()
    with engine.connect() as conn:
        _create_fleet_assets_old_0005_shape(conn)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
        with Operations.context(ctx):
            module.downgrade()

        columns = {col['name'] for col in sa.inspect(conn).get_columns('fleet_assets')}
        assert {'latitude', 'longitude', 'last_telemetry_at'} <= columns
