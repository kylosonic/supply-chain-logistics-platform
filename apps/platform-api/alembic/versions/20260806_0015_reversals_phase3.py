"""Reversals Phase 3: reversal columns, wallet void status, fraud flags.

Revision ID: 20260806_0015
Revises: 20260806_0014
Create Date: 2026-08-06 00:00:00.000000

SQLITE QUIRK (empirically verified on SQLAlchemy 2.0.36 / alembic 1.14.1):
constraint drop/add (and batch mode — its table reflection captures CHECK
expressions with a trailing extra paren) are NOT viable on sqlite, so the
CHECK/FK constraint DDL below is Postgres-only. sqlite runs get the new
columns and the ``sender_fraud_flags`` table only; the model CheckConstraints
are authoritative for test databases, which build via
``Base.metadata.create_all`` (Phase 2 precedent). ``alembic upgrade head``
on a sqlite-stamped schema therefore succeeds but does not enforce the
CHECK constraints at the DB level.
"""
import sqlalchemy as sa
from alembic import op

revision = '20260806_0015'
down_revision = '20260806_0014'
branch_labels = None
depends_on = None


def _reversal_columns_sqlite() -> None:
    """Columns only (sqlite cannot add CHECK/FK constraints post-hoc)."""
    op.add_column('payment_receipts', sa.Column('reversal_status', sa.String(length=16), nullable=True))
    op.add_column('payment_receipts', sa.Column('reversal_note', sa.String(length=512), nullable=True))
    op.add_column('payment_receipts', sa.Column('reversed_by_user_id', sa.CHAR(length=36), nullable=True))
    op.add_column('payment_receipts', sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('wallet_credits', sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True))


def _reversal_columns_postgres() -> None:
    op.add_column('payment_receipts', sa.Column('reversal_status', sa.String(length=16), nullable=True))
    op.add_column('payment_receipts', sa.Column('reversal_note', sa.String(length=512), nullable=True))
    op.add_column('payment_receipts', sa.Column('reversed_by_user_id', sa.CHAR(length=36), nullable=True))
    op.add_column('payment_receipts', sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        'ck_payment_receipt_reversal_status',
        'payment_receipts',
        "reversal_status IN ('undo','reversed') OR reversal_status IS NULL",
    )
    op.create_foreign_key(
        'fk_payment_receipts_reversed_by_user',
        'payment_receipts',
        'users',
        ['reversed_by_user_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.add_column('wallet_credits', sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint('ck_wallet_credit_status', 'wallet_credits', type_='check')
    op.create_check_constraint(
        'ck_wallet_credit_status', 'wallet_credits', "status IN ('available','applied','voided')"
    )


def _create_fraud_flags_table() -> None:
    op.create_table(
        'sender_fraud_flags',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('sender_name', sa.String(length=128), nullable=False),
        sa.Column('fraud_risk_since', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reversal_count', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'sender_name', name='uq_sender_fraud_flag_org_sender'),
    )
    op.create_index('ix_sender_fraud_flags_organization_id', 'sender_fraud_flags', ['organization_id'])


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        _reversal_columns_sqlite()
    else:
        _reversal_columns_postgres()
    _create_fraud_flags_table()


def downgrade() -> None:
    op.drop_index('ix_sender_fraud_flags_organization_id', table_name='sender_fraud_flags')
    op.drop_table('sender_fraud_flags')
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.drop_column('payment_receipts', 'reversed_at')
        op.drop_column('payment_receipts', 'reversed_by_user_id')
        op.drop_column('payment_receipts', 'reversal_note')
        op.drop_column('payment_receipts', 'reversal_status')
        op.drop_column('wallet_credits', 'voided_at')
    else:
        op.drop_column('payment_receipts', 'reversed_at')
        op.drop_column('payment_receipts', 'reversed_by_user_id')
        op.drop_column('payment_receipts', 'reversal_note')
        op.drop_column('payment_receipts', 'reversal_status')
        op.drop_column('wallet_credits', 'voided_at')
        op.drop_constraint('ck_wallet_credit_status', 'wallet_credits', type_='check')
        op.create_check_constraint(
            'ck_wallet_credit_status', 'wallet_credits', "status IN ('available','applied')"
        )
