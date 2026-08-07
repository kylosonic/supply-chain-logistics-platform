"""TDD regression test for the 0013 ``_backfill_organizations`` INSERT bind.

The untyped ``sa.text()`` INSERT binds a raw ``uuid.UUID`` for
``trial_records.id``. The sqlite3 driver rejects that with
``sqlite3.ProgrammingError: type 'UUID' is not supported`` — unless a
process-global ``sqlite3.register_adapter(UUID, str)`` was registered first.

The app registers such an adapter in ``app/db/session.py`` (imported by the
FastAPI runtime), but the alembic ``env.py`` chain never imports it, so
stamped sqlite chains executed via ``alembic upgrade`` run in a fresh
interpreter WITHOUT the adapter — and fail. Because pytest's ``conftest.py``
imports ``app.main`` (which registers the adapter process-wide), the only
faithful in-suite reproduction is a subprocess with a clean interpreter.

This test is RED on the unguarded code and green after fix ① (blueprint §2c).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_CHILD_SCRIPT = r'''
import importlib.util
import sys
from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.pool import StaticPool

root = Path(sys.argv[1])
sys.path.insert(0, str(root))

spec = importlib.util.spec_from_file_location(
    'child_0013_mod', root / 'alembic' / 'versions' / '20260805_0013_cashflow_phase1.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

engine = sa.create_engine(
    'sqlite+pysqlite:///:memory:',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
with engine.connect() as conn:
    conn.execute(
        sa.text(
            'CREATE TABLE organizations ('
            'id VARCHAR NOT NULL, name VARCHAR(128) NOT NULL, slug VARCHAR(64) NOT NULL, '
            'subscription_tier VARCHAR(24) NOT NULL, subscription_status VARCHAR(24) NOT NULL, '
            "billing_phase VARCHAR(24) NOT NULL DEFAULT 'free', "
            'trial_started_at DATETIME, trial_ends_at DATETIME, '
            'is_active BOOLEAN NOT NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, '
            'PRIMARY KEY (id)'
            ')'
        )
    )
    conn.execute(
        sa.text(
            'CREATE TABLE trial_records ('
            'id UUID NOT NULL, organization_id UUID NOT NULL, tier VARCHAR(24) NOT NULL, '
            'started_at DATETIME NOT NULL, ended_at DATETIME, created_at DATETIME NOT NULL, '
            'PRIMARY KEY (id)'
            ')'
        )
    )
    conn.execute(
        sa.text(
            'INSERT INTO organizations (id, name, slug, subscription_tier, subscription_status, '
            'is_active, created_at, updated_at) '
            'VALUES (:id, :name, :slug, :tier, :status, :active, :ts, :ts)'
        ),
        {
            'id': 'org-trialing-1',
            'name': 'Trialing Co',
            'slug': 'trialing-co',
            'tier': 'starter',
            'status': 'trialing',
            'active': True,
            'ts': '2026-08-05 00:00:00',
        },
    )

    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        module._backfill_organizations()  # noqa: SLF001 -- unit under test

    rows = conn.execute(sa.text('SELECT id FROM trial_records')).fetchall()
    if len(rows) != 1:
        raise AssertionError(f'expected 1 trial_records row, got {len(rows)}')
    UUID(str(rows[0].id))
print('BACKFILL_OK')
'''


def test_0013_backfill_binds_new_ids_on_sqlite():
    """Clean-interpreter proof: no app adapter masks the raw-UUID bind."""
    result = subprocess.run(
        [sys.executable, '-c', _CHILD_SCRIPT, str(_PROJECT_ROOT)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f'0013 backfill failed in a clean sqlite interpreter:\n'
        f'{result.stdout}\n{result.stderr}'
    )
    assert 'BACKFILL_OK' in result.stdout
