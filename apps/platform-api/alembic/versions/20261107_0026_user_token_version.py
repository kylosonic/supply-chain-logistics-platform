"""Add per-user token version for server-side logout revocation.

Revision ID: 20261107_0026
Revises: 20261107_0025
Create Date: 2026-11-07 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = '20261107_0026'
down_revision = '20261107_0025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {
        column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')
    }
    if 'token_version' not in columns:
        with op.batch_alter_table('users') as batch_op:
            batch_op.add_column(
                sa.Column(
                    'token_version',
                    sa.Integer(),
                    nullable=False,
                    server_default='0',
                )
            )


def downgrade() -> None:
    columns = {
        column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')
    }
    if 'token_version' in columns:
        with op.batch_alter_table('users') as batch_op:
            batch_op.drop_column('token_version')
