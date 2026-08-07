"""Cashflow Phase 1: billing tables, trial fields, collection accounts.

Revision ID: 20260805_0013
Revises: 20260803_0012
Create Date: 2026-08-05 00:00:00.000000

NOTE: collection-account seed values come from env fields
(CBE_ACCOUNT_HOLDER / CBE_ACCOUNT_NUMBER / DASHEN_ACCOUNT_HOLDER /
DASHEN_ACCOUNT_NUMBER) when present, else placeholder constants below.
The placeholder account numbers MUST be replaced with the real CBE and
Dashen collection account details before production launch (NB-02).
"""
import uuid
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.config import settings

revision = '20260805_0013'
down_revision = '20260803_0012'
branch_labels = None
depends_on = None

_PLACEHOLDER_CBE_NUMBER = '1000000000000'
_PLACEHOLDER_DASHEN_NUMBER = '0000000000000'


def _collection_account_seeds() -> list[dict]:
    return [
        {
            'bank_code': 'cbe',
            'bank_name': 'Commercial Bank of Ethiopia',
            'account_holder': settings.cbe_account_holder or 'FreightPilot PLC',
            'account_number': settings.cbe_account_number or _PLACEHOLDER_CBE_NUMBER,
        },
        {
            'bank_code': 'dashen',
            'bank_name': 'Dashen Bank S.C.',
            'account_holder': settings.dashen_account_holder or 'FreightPilot PLC',
            'account_number': settings.dashen_account_number or _PLACEHOLDER_DASHEN_NUMBER,
        },
    ]


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)

    # --- collection_accounts -------------------------------------------------
    op.create_table(
        'collection_accounts',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('bank_code', sa.String(length=16), nullable=False),
        sa.Column('bank_name', sa.String(length=64), nullable=False),
        sa.Column('account_holder', sa.String(length=128), nullable=False),
        sa.Column('account_number', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("bank_code IN ('cbe', 'dashen')", name='ck_collection_account_bank_code'),
        sa.UniqueConstraint('bank_code', name='uq_collection_account_bank_code'),
    )

    # --- subscription_invoices ------------------------------------------------
    op.create_table(
        'subscription_invoices',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('organization_id', uuid_type, nullable=False),
        sa.Column('invoice_number', sa.String(length=32), nullable=False),
        sa.Column('tier', sa.String(length=24), nullable=False),
        sa.Column('billing_period_start', sa.Date(), nullable=False),
        sa.Column('billing_period_end', sa.Date(), nullable=False),
        sa.Column('flat_amount_etb', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total_etb', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('balance_remaining_etb', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('grace_days', sa.Integer(), nullable=False),
        sa.Column('grace_ends_at', sa.Date(), nullable=False),
        sa.Column('designated_account_id', uuid_type, nullable=False),
        sa.Column('status', sa.String(length=24), server_default='issued', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['designated_account_id'], ['collection_accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number', name='uq_subscription_invoice_number'),
        sa.UniqueConstraint(
            'organization_id', 'billing_period_start', name='uq_subscription_invoice_org_period'
        ),
    )
    op.create_index(
        'ix_subscription_invoices_organization_id', 'subscription_invoices', ['organization_id']
    )
    op.create_index('ix_subscription_invoices_invoice_number', 'subscription_invoices', ['invoice_number'])

    # --- invoice_line_items ---------------------------------------------------
    op.create_table(
        'invoice_line_items',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('invoice_id', uuid_type, nullable=False),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('description', sa.String(length=128), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit_price_etb', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('amount_etb', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['subscription_invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoice_line_items_invoice_id', 'invoice_line_items', ['invoice_id'])

    # --- trial_records ----------------------------------------------------------
    op.create_table(
        'trial_records',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('organization_id', uuid_type, nullable=False),
        sa.Column('tier', sa.String(length=24), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'tier', name='uq_trial_record_org_tier'),
    )
    op.create_index('ix_trial_records_organization_id', 'trial_records', ['organization_id'])

    # --- notifications ------------------------------------------------------------
    op.create_table(
        'notifications',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('organization_id', uuid_type, nullable=False),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('message', sa.String(length=512), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_organization_id', 'notifications', ['organization_id'])
    op.create_index(
        'ix_notifications_org_kind_expires', 'notifications', ['organization_id', 'kind', 'expires_at']
    )

    # --- billing_counters (single-row sequence) ----------------------------------
    op.create_table(
        'billing_counters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('last_value', sa.Integer(), server_default='0', nullable=False),
    )
    op.bulk_insert(sa.table('billing_counters', sa.column('id', sa.Integer), sa.column('last_value', sa.Integer)), [{'id': 1, 'last_value': 0}])

    # --- organizations: trial fields --------------------------------------------
    op.add_column('organizations', sa.Column('billing_phase', sa.String(length=24), server_default='free', nullable=False))
    op.add_column('organizations', sa.Column('trial_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('organizations', sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True))

    # --- seed collection accounts --------------------------------------------------
    for seed in _collection_account_seeds():
        op.bulk_insert(
            sa.table(
                'collection_accounts',
                sa.column('id', uuid_type),
                sa.column('bank_code', sa.String(16)),
                sa.column('bank_name', sa.String(64)),
                sa.column('account_holder', sa.String(128)),
                sa.column('account_number', sa.String(64)),
                sa.column('is_active', sa.Boolean()),
            ),
            [{**seed, 'id': uuid.uuid4(), 'is_active': True}],
        )

    # --- backfill existing orgs (no fabricated invoices) ---------------------------
    _backfill_organizations()


def _backfill_organizations() -> None:
    """Map legacy subscription_status onto the new phase model.

    trialing -> trial + a FRESH TrialRecord(now, now+168h); active -> active;
    past_due -> hard_locked; canceled -> free. No invoices are fabricated.
    """
    bind = op.get_bind()
    rows = bind.execute(sa.text('SELECT id, subscription_tier, subscription_status FROM organizations')).fetchall()
    now = datetime.now(UTC)
    for org_id, tier, status in rows:
        if status == 'trialing':
            started = now
            ended = now + timedelta(hours=168)
            bind.execute(
                sa.text(
                    'UPDATE organizations SET billing_phase = :phase, '
                    'trial_started_at = :started, trial_ends_at = :ended WHERE id = :org_id'
                ),
                {'phase': 'trial', 'started': started, 'ended': ended, 'org_id': org_id},
            )
            bind.execute(
                sa.text(
                    'INSERT INTO trial_records (id, organization_id, tier, started_at, ended_at, created_at) '
                    'VALUES (:id, :org_id, :tier, :started, :ended, :created)'
                ),
                {
                    # Dialect guard: sqlite3 rejects raw uuid.UUID binds, and
                    # PostgreSQL has no text->uuid assignment cast — so only
                    # sqlite receives the str() form (fix ①, TECH-54).
                    'id': str(uuid.uuid4()) if bind.dialect.name == 'sqlite' else uuid.uuid4(),
                    'org_id': org_id,
                    'tier': tier or 'starter',
                    'started': started,
                    'ended': ended,
                    'created': now,
                },
            )
        elif status == 'active':
            bind.execute(
                sa.text('UPDATE organizations SET billing_phase = :phase WHERE id = :org_id'),
                {'phase': 'active', 'org_id': org_id},
            )
        elif status == 'past_due':
            bind.execute(
                sa.text('UPDATE organizations SET billing_phase = :phase WHERE id = :org_id'),
                {'phase': 'hard_locked', 'org_id': org_id},
            )
        elif status == 'canceled':
            bind.execute(
                sa.text('UPDATE organizations SET billing_phase = :phase WHERE id = :org_id'),
                {'phase': 'free', 'org_id': org_id},
            )


def downgrade() -> None:
    op.drop_table('invoice_line_items')
    op.drop_table('subscription_invoices')
    op.drop_table('trial_records')
    op.drop_table('notifications')
    op.drop_table('billing_counters')
    op.drop_table('collection_accounts')
    op.drop_column('organizations', 'trial_ends_at')
    op.drop_column('organizations', 'trial_started_at')
    op.drop_column('organizations', 'billing_phase')
