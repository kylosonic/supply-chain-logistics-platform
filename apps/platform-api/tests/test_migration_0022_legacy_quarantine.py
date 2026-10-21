from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa

MIGRATION_PATH = (
    Path(__file__).resolve().parent.parent
    / 'alembic'
    / 'versions'
    / '20260821_0022_quarantine_legacy_null_org.py'
)


class _FakeOp:
    def __init__(self, connection: sa.Connection):
        self._connection = connection

    def get_bind(self) -> sa.Connection:
        return self._connection


def _load_migration():
    spec = importlib.util.spec_from_file_location('migration_0022', MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                'CREATE TABLE organizations ('
                'id VARCHAR(36) PRIMARY KEY, name VARCHAR(128) NOT NULL, '
                'slug VARCHAR(64) NOT NULL UNIQUE, primary_email_domain VARCHAR(255), '
                'subscription_tier VARCHAR(24) NOT NULL, subscription_status VARCHAR(24) NOT NULL, '
                'billing_phase VARCHAR(24) NOT NULL, is_active BOOLEAN NOT NULL, '
                'created_at DATETIME DEFAULT CURRENT_TIMESTAMP, '
                'updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)'
            )
        )
        connection.execute(
            sa.text(
                'CREATE TABLE warehouses ('
                'id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) NOT NULL, '
                'organization_id VARCHAR(36))'
            )
        )


def test_null_org_rows_are_preserved_in_quarantine_and_reversible():
    engine = sa.create_engine('sqlite+pysqlite:///:memory:')
    _schema(engine)
    with engine.begin() as connection:
        connection.execute(
            sa.text("INSERT INTO warehouses (id, code, organization_id) VALUES ('w1', 'LEGACY', NULL)")
        )
        migration = _load_migration()
        migration.op = _FakeOp(connection)
        migration.upgrade()

        org_id = connection.execute(
            sa.text("SELECT id FROM organizations WHERE slug = 'legacy-unassigned-data'")
        ).scalar_one()
        warehouse_org = connection.execute(
            sa.text("SELECT organization_id FROM warehouses WHERE id = 'w1'")
        ).scalar_one()
        assert str(warehouse_org) == str(org_id)

        migration.downgrade()
        assert connection.execute(sa.text('SELECT COUNT(*) FROM organizations')).scalar_one() == 0
        assert (
            connection.execute(sa.text("SELECT organization_id FROM warehouses WHERE id = 'w1'")).scalar_one()
            is None
        )


def test_no_quarantine_org_is_created_when_no_null_rows_exist():
    engine = sa.create_engine('sqlite+pysqlite:///:memory:')
    _schema(engine)
    with engine.begin() as connection:
        migration = _load_migration()
        migration.op = _FakeOp(connection)
        migration.upgrade()
        assert connection.execute(sa.text('SELECT COUNT(*) FROM organizations')).scalar_one() == 0


def test_quarantine_slug_collision_fails_without_taking_over_data():
    engine = sa.create_engine('sqlite+pysqlite:///:memory:')
    _schema(engine)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO organizations ("
                "id, name, slug, primary_email_domain, subscription_tier, "
                "subscription_status, billing_phase, is_active"
                ") VALUES ("
                "'11111111-1111-4111-8111-111111111111', "
                "'Attacker-owned workspace', 'legacy-unassigned-data', "
                "NULL, 'free', 'active', 'free', 1"
                ")"
            )
        )
        connection.execute(
            sa.text("INSERT INTO warehouses (id, code, organization_id) VALUES ('w1', 'LEGACY', NULL)")
        )
        migration = _load_migration()
        migration.op = _FakeOp(connection)
        with pytest.raises(RuntimeError, match='identity conflict'):
            migration.upgrade()
        assert (
            connection.execute(
                sa.text("SELECT organization_id FROM warehouses WHERE id = 'w1'")
            ).scalar_one()
            is None
        )
