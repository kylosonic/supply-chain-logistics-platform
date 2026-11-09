"""Add auditable dispatch cash handover and deposit evidence.

Revision ID: 20261107_0025
Revises: 20260823_0024
Create Date: 2026-11-07 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op
from app.db.custom_types import UUIDType

revision = '20261107_0025'
down_revision = '20260823_0024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('dispatch_runs') as batch_op:
        batch_op.add_column(
            sa.Column(
                'cash_closed_by_user_id',
                UUIDType(),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            'fk_dispatch_runs_cash_closed_by_user_id_users',
            'users',
            ['cash_closed_by_user_id'],
            ['id'],
            ondelete='SET NULL',
        )
        batch_op.add_column(sa.Column('cash_declared_etb', sa.Numeric(14, 2), nullable=True))
        batch_op.add_column(sa.Column('cash_handed_over_etb', sa.Numeric(14, 2), nullable=True))
        batch_op.add_column(sa.Column('cash_shortfall_etb', sa.Numeric(14, 2), nullable=True))
        batch_op.add_column(sa.Column('cash_overage_etb', sa.Numeric(14, 2), nullable=True))
        batch_op.add_column(sa.Column('cash_deposit_bank', sa.String(length=16), nullable=True))
        batch_op.add_column(
            sa.Column('cash_deposit_reference', sa.String(length=128), nullable=True)
        )
        batch_op.add_column(sa.Column('cash_close_note', sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('dispatch_runs') as batch_op:
        batch_op.drop_column('cash_close_note')
        batch_op.drop_column('cash_deposit_reference')
        batch_op.drop_column('cash_deposit_bank')
        batch_op.drop_column('cash_overage_etb')
        batch_op.drop_column('cash_shortfall_etb')
        batch_op.drop_column('cash_handed_over_etb')
        batch_op.drop_column('cash_declared_etb')
        batch_op.drop_constraint(
            'fk_dispatch_runs_cash_closed_by_user_id_users',
            type_='foreignkey',
        )
        batch_op.drop_column('cash_closed_by_user_id')
