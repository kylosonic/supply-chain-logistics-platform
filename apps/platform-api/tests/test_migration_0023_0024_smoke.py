from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic.config import Config

from alembic import command
from app.core.config import settings
from app.db.base import Base
from app.models.driver import Driver
from app.models.item import Item
from app.models.organization import Organization
from app.models.user import User

_ROOT = Path(__file__).resolve().parent.parent


def test_dispatch_and_invitation_migrations_upgrade_and_downgrade(tmp_path, monkeypatch):
    database = tmp_path / 'migration-smoke.db'
    engine = sa.create_engine(f'sqlite+pysqlite:///{database.as_posix()}')
    Base.metadata.create_all(
        engine,
        tables=[Organization.__table__, User.__table__, Driver.__table__, Item.__table__],
    )

    monkeypatch.setattr(settings, 'database_url', f'sqlite+pysqlite:///{database.as_posix()}')
    config = Config(str(_ROOT / 'alembic.ini'))

    command.stamp(config, '20260813_0021')
    command.upgrade(config, 'head')

    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())
    expected_tables = {
        'organization_invitations',
        'customers',
        'dispatch_runs',
        'delivery_orders',
        'delivery_proofs',
    }
    assert expected_tables <= tables
    assert 'unassigned_json' in {
        column['name'] for column in inspector.get_columns('dispatch_runs')
    }
    assert 'proof_sequence' in {
        column['name'] for column in inspector.get_columns('delivery_proofs')
    }

    command.downgrade(config, '20260813_0021')
    tables_after = set(sa.inspect(engine).get_table_names())
    assert not expected_tables & tables_after
