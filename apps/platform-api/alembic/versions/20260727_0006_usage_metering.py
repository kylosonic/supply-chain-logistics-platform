"""add organization usage metering table

Revision ID: 20260727_0006
Revises: 20260727_0005
Create Date: 2026-07-27 00:06:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260727_0006'
down_revision = '20260727_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'organization_usage_counters',
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('metric', sa.String(length=48), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('used_units', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'metric', 'period_start', name='uq_usage_org_metric_period_start'),
    )

    op.create_index(
        op.f('ix_organization_usage_counters_organization_id'),
        'organization_usage_counters',
        ['organization_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_organization_usage_counters_metric'),
        'organization_usage_counters',
        ['metric'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_organization_usage_counters_metric'), table_name='organization_usage_counters')
    op.drop_index(op.f('ix_organization_usage_counters_organization_id'), table_name='organization_usage_counters')
    op.drop_table('organization_usage_counters')
