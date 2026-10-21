"""Add the persisted route decision explanation.

Revision ID: 20260813_0021
Revises: 20260812_0020
Create Date: 2026-08-13 00:00:00.000000

The explanation is nullable and computed only for new runs. Older runs keep
serving normally and report that no explanation was recorded.
"""

import sqlalchemy as sa

from alembic import op

revision = '20260813_0021'
down_revision = '20260812_0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'route_optimization_runs',
        sa.Column('explanation_json', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('route_optimization_runs', 'explanation_json')
