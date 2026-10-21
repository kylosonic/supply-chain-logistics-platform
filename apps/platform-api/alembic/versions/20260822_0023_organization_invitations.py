"""Add workspace invitations.

Revision ID: 20260822_0023
Revises: 20260821_0022
Create Date: 2026-10-21 00:00:00.000000
"""

# ruff: noqa: E501

import sqlalchemy as sa

from alembic import op
from app.db.custom_types import UUIDType

revision = '20260822_0023'
down_revision = '20260821_0022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'organization_invitations',
        sa.Column('id', UUIDType(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'organization_id',
            UUIDType(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=24), server_default='viewer', nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column(
            'invited_by_user_id', UUIDType(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
        ),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'accepted_by_user_id', UUIDType(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
        ),
        sa.Column('status', sa.String(length=16), server_default='pending', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('token_hash', name='uq_organization_invitations_token_hash'),
    )
    op.create_index(
        'ix_organization_invitations_organization_id', 'organization_invitations', ['organization_id']
    )
    op.create_index('ix_organization_invitations_email', 'organization_invitations', ['email'])
    op.create_index('ix_organization_invitations_token_hash', 'organization_invitations', ['token_hash'])
    op.create_index(
        'ix_org_invitations_org_status',
        'organization_invitations',
        ['organization_id', 'status'],
    )
    op.create_index(
        'ix_org_invitations_email_status',
        'organization_invitations',
        ['email', 'status'],
    )


def downgrade() -> None:
    op.drop_index('ix_org_invitations_email_status', table_name='organization_invitations')
    op.drop_index('ix_org_invitations_org_status', table_name='organization_invitations')
    op.drop_index('ix_organization_invitations_token_hash', table_name='organization_invitations')
    op.drop_index('ix_organization_invitations_email', table_name='organization_invitations')
    op.drop_index('ix_organization_invitations_organization_id', table_name='organization_invitations')
    op.drop_table('organization_invitations')
