"""Backfill missing fleet_assets telemetry columns on existing databases.

Revision ID: 20260806_0017
Revises: 20260806_0016
Create Date: 2026-08-06 00:00:01.000000

The historical ``20260727_0005_fleet_assets`` migration originally created
``fleet_assets`` without ``latitude``, ``longitude``, or
``last_telemetry_at``. Runtime seeding now writes those model-backed columns,
so already-created databases need a forward repair. Fresh databases already
receive the columns from the corrected historical migration, therefore this
revision is intentionally idempotent.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = '20260806_0017'
down_revision = '20260806_0016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {column['name'] for column in inspector.get_columns('fleet_assets')}

    if 'latitude' not in existing:
        op.add_column('fleet_assets', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in existing:
        op.add_column('fleet_assets', sa.Column('longitude', sa.Float(), nullable=True))
    if 'last_telemetry_at' not in existing:
        op.add_column('fleet_assets', sa.Column('last_telemetry_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # No-op: the corrected historical migration now defines these columns for
    # fresh schemas, so removing them would create needless divergence.
    return None