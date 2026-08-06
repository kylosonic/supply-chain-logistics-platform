"""Receipt Processing Phase 2: receipts, extraction, wallet, SMS, disputes.

Revision ID: 20260806_0014
Revises: 20260805_0013
Create Date: 2026-08-06 00:00:00.000000

NOTE (portability): the partial unique index
``uq_payment_receipt_verified_ref`` is declared with BOTH
``postgresql_where`` and ``sqlite_where`` so ``Base.metadata.create_all``
and sqlite test databases build it. If the bundled sqlite version ever
rejects partial indexes during ``alembic upgrade head`` on sqlite, keep
the index Postgres-only and rely on the service-layer dedup + IntegrityError
backstop (blueprint §11.5).
"""
import sqlalchemy as sa
from alembic import op

revision = '20260806_0014'
down_revision = '20260805_0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- payment_receipts ---------------------------------------------------
    op.create_table(
        'payment_receipts',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('invoice_id', sa.CHAR(length=36), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=64), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('file_sha256', sa.String(length=64), nullable=False),
        sa.Column('reference_number', sa.String(length=64), nullable=True),
        sa.Column('amount_etb', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('sender_name', sa.String(length=128), nullable=True),
        sa.Column('sender_account_number', sa.String(length=64), nullable=True),
        sa.Column('receiver_account_number', sa.String(length=64), nullable=True),
        sa.Column('receiver_name', sa.String(length=128), nullable=True),
        sa.Column('transfer_date', sa.Date(), nullable=True),
        sa.Column('bank_code', sa.String(length=16), nullable=True),
        sa.Column('status', sa.String(length=24), server_default='pending', nullable=False),
        sa.Column('verdict', sa.String(length=24), nullable=True),
        sa.Column('rejection_reason', sa.String(length=512), nullable=True),
        sa.Column('admin_note', sa.String(length=512), nullable=True),
        sa.Column('decision_made_by_user_id', sa.CHAR(length=36), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trusted_payer_action', sa.String(length=24), nullable=True),
        sa.Column('large_surplus_decision', sa.String(length=24), nullable=True),
        sa.Column('partial_credit_amount_etb', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('surplus_etb', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('is_new_sender', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('is_cash_sender', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column(
            'is_wrong_bank_within_portfolio', sa.Boolean(), server_default=sa.text('0'), nullable=False
        ),
        sa.Column('is_large_surplus', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('is_duplicate', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('has_zero_confidence', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('low_confidence_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending','verified','rejected','escalated')", name='ck_payment_receipt_status'
        ),
        sa.CheckConstraint(
            "verdict IN ('verify','reject_wrong_bank','reject_duplicate','reject_illegible','escalate') "
            'OR verdict IS NULL',
            name='ck_payment_receipt_verdict',
        ),
        sa.CheckConstraint(
            "trusted_payer_action IN ('added','verified_once') OR trusted_payer_action IS NULL",
            name='ck_payment_receipt_trusted_payer_action',
        ),
        sa.CheckConstraint(
            "large_surplus_decision IN ('credit_forward','credit_backward','partial_ignore') "
            'OR large_surplus_decision IS NULL',
            name='ck_payment_receipt_large_surplus_decision',
        ),
        sa.ForeignKeyConstraint(['invoice_id'], ['subscription_invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decision_made_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_payment_receipts_organization_id', 'payment_receipts', ['organization_id']
    )
    op.create_index('ix_payment_receipts_invoice_id', 'payment_receipts', ['invoice_id'])
    op.create_index('ix_payment_receipts_reference_number', 'payment_receipts', ['reference_number'])
    op.create_index(
        'ix_payment_receipts_org_status', 'payment_receipts', ['organization_id', 'status']
    )
    op.create_index(
        'ix_payment_receipts_status_created', 'payment_receipts', ['status', 'created_at']
    )
    op.create_index(
        'uq_payment_receipt_verified_ref',
        'payment_receipts',
        ['reference_number'],
        unique=True,
        postgresql_where=sa.text("status = 'verified'"),
        sqlite_where=sa.text("status = 'verified'"),
    )

    # --- receipt_extractions --------------------------------------------------
    op.create_table(
        'receipt_extractions',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('receipt_id', sa.CHAR(length=36), nullable=False),
        sa.Column('provider_name', sa.String(length=64), nullable=True),
        sa.Column('key_id', sa.String(length=64), nullable=True),
        sa.Column('model_name', sa.String(length=64), nullable=True),
        sa.Column('fields', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.JSON(), nullable=False),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['receipt_id'], ['payment_receipts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('receipt_id', name='uq_receipt_extraction_receipt'),
    )

    # --- wallet_credits ---------------------------------------------------------
    op.create_table(
        'wallet_credits',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('receipt_id', sa.CHAR(length=36), nullable=False),
        sa.Column('amount_etb', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('status', sa.String(length=16), server_default='available', nullable=False),
        sa.Column('applied_to_invoice_id', sa.CHAR(length=36), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('amount_etb > 0', name='ck_wallet_credit_amount_positive'),
        sa.CheckConstraint("status IN ('available','applied')", name='ck_wallet_credit_status'),
        sa.ForeignKeyConstraint(
            ['applied_to_invoice_id'], ['subscription_invoices.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receipt_id'], ['payment_receipts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wallet_credits_organization_id', 'wallet_credits', ['organization_id'])
    op.create_index('ix_wallet_credits_org_status', 'wallet_credits', ['organization_id', 'status'])

    # --- sms_messages ------------------------------------------------------------
    op.create_table(
        'sms_messages',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('receipt_id', sa.CHAR(length=36), nullable=True),
        sa.Column('to_phone', sa.String(length=24), nullable=False),
        sa.Column('body', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=16), server_default='queued', nullable=False),
        sa.Column('provider_name', sa.String(length=64), nullable=True),
        sa.Column('gateway_message_id', sa.String(length=128), nullable=True),
        sa.Column('error_message', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued','sent','failed')", name='ck_sms_message_status'),
        sa.CheckConstraint('length(body) <= 200', name='ck_sms_message_body_length'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receipt_id'], ['payment_receipts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sms_messages_organization_id', 'sms_messages', ['organization_id'])

    # --- trusted_payers -------------------------------------------------------------
    op.create_table(
        'trusted_payers',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('sender_name', sa.String(length=128), nullable=False),
        sa.Column('added_by_user_id', sa.CHAR(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'sender_name', name='uq_trusted_payer_org_sender'),
    )
    op.create_index('ix_trusted_payers_organization_id', 'trusted_payers', ['organization_id'])

    # --- dispute_threads ---------------------------------------------------------------
    op.create_table(
        'dispute_threads',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('receipt_id', sa.CHAR(length=36), nullable=False),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('dispute_text', sa.String(length=1000), nullable=False),
        sa.Column('submitted_by_user_id', sa.CHAR(length=36), nullable=True),
        sa.Column('status', sa.String(length=16), server_default='open', nullable=False),
        sa.Column('resolution', sa.String(length=24), nullable=True),
        sa.Column('resolved_by_user_id', sa.CHAR(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('open','resolved')", name='ck_dispute_thread_status'),
        sa.CheckConstraint(
            "resolution IN ('verify','maintain_rejection') OR resolution IS NULL",
            name='ck_dispute_thread_resolution',
        ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receipt_id'], ['payment_receipts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submitted_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('receipt_id', name='uq_dispute_thread_receipt'),
    )
    op.create_index('ix_dispute_threads_organization_id', 'dispute_threads', ['organization_id'])

    # --- organizations: contact_phone -------------------------------------------------
    op.add_column('organizations', sa.Column('contact_phone', sa.String(length=24), nullable=True))


def downgrade() -> None:
    op.drop_column('organizations', 'contact_phone')
    op.drop_table('dispute_threads')
    op.drop_table('trusted_payers')
    op.drop_table('sms_messages')
    op.drop_table('wallet_credits')
    op.drop_table('receipt_extractions')
    op.drop_table('payment_receipts')
