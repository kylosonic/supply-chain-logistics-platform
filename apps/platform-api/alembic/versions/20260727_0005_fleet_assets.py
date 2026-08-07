"""add fleet assets table

Revision ID: 20260727_0005
Revises: 20260727_0004
Create Date: 2026-07-27 00:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260727_0005'
down_revision = '20260727_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'fleet_assets',
        sa.Column('vehicle_code', sa.String(length=64), nullable=False),
        sa.Column('driver_name', sa.String(length=128), nullable=False),
        sa.Column('driver_contact', sa.String(length=128), nullable=True),
        sa.Column('capacity_units', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('last_telemetry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_fleet_assets_vehicle_code'), 'fleet_assets', ['vehicle_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_fleet_assets_vehicle_code'), table_name='fleet_assets')
    op.drop_table('fleet_assets')
