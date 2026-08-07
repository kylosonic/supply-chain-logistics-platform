"""Repair model/migration drift — add columns declared in models but never
created by any migration.

Revision ID: 20260808_0018
Revises: 20260806_0017
Create Date: 2026-08-08 00:00:01.000000

Drift discovered 2026-08-07 via model-vs-prod schema audit after the live
``POST /routes/optimize`` persist path returned 500 on alembic-built Postgres
(INSERT into ``route_schedules`` hit ``UndefinedColumn``). Unit tests never
caught it because sqlite test schemas come from ``Base.metadata.create_all``,
which is model-authoritative.

Missing columns (all nullable-additive except noted):
- ``route_schedules.assigned_asset_id`` — uuid, FK ``fleet_assets.id`` SET NULL
- ``route_schedules.origin_latitude`` / ``origin_longitude`` — float, nullable
- ``alerts.payload`` — json, nullable
- ``shipments.scope_3_emissions_kg`` — float, NOT NULL, ``server_default '0'``
  (matches the model's ``default=0.0``)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = '20260808_0018'
down_revision = '20260806_0017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    route_cols = {column['name'] for column in inspector.get_columns('route_schedules')}
    if 'assigned_asset_id' not in route_cols:
        op.add_column('route_schedules', sa.Column('assigned_asset_id', sa.Uuid(), nullable=True))
    if 'origin_latitude' not in route_cols:
        op.add_column('route_schedules', sa.Column('origin_latitude', sa.Float(), nullable=True))
    if 'origin_longitude' not in route_cols:
        op.add_column('route_schedules', sa.Column('origin_longitude', sa.Float(), nullable=True))
    if bind.dialect.name != 'sqlite':
        # FK constraint — sqlite batch mode emits malformed DDL (documented
        # precedent in 0015); models stay authoritative on sqlite test paths.
        op.create_foreign_key(
            'fk_route_schedules_assigned_asset',
            'route_schedules',
            'fleet_assets',
            ['assigned_asset_id'],
            ['id'],
            ondelete='SET NULL',
        )

    alert_cols = {column['name'] for column in inspector.get_columns('alerts')}
    if 'payload' not in alert_cols:
        op.add_column('alerts', sa.Column('payload', sa.JSON(), nullable=True))

    shipment_cols = {column['name'] for column in inspector.get_columns('shipments')}
    if 'scope_3_emissions_kg' not in shipment_cols:
        op.add_column(
            'shipments',
            sa.Column('scope_3_emissions_kg', sa.Float(), nullable=False, server_default='0'),
        )


def downgrade() -> None:
    # No-op: models are authoritative; the columns are additive and the
    # historical migrations never created them, so removal would re-open the
    # drift this revision exists to close.
    return None
