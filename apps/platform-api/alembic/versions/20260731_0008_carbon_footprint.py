"""add minimize_carbon_footprint to route optimization runs

Revision ID: 20260731_0008
Revises: 20260729_0007
Create Date: 2026-07-31 21:26:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260731_0008'
down_revision = '20260729_0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('route_optimization_runs', sa.Column('minimize_carbon_footprint', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('route_optimization_runs', sa.Column('co2_saved_kg', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('route_optimization_runs', 'co2_saved_kg')
    op.drop_column('route_optimization_runs', 'minimize_carbon_footprint')
