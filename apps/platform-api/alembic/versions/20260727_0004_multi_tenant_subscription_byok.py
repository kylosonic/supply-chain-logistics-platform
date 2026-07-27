"""add organizations memberships and provider keys

Revision ID: 20260727_0004
Revises: 20260524_0003
Create Date: 2026-07-27 00:04:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260727_0004'
down_revision = '20260524_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('full_name', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'organizations',
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('primary_email_domain', sa.String(length=255), nullable=True),
        sa.Column('subscription_tier', sa.String(length=24), nullable=False),
        sa.Column('subscription_status', sa.String(length=24), nullable=False),
        sa.Column('preferred_ai_provider', sa.String(length=64), nullable=True),
        sa.Column('preferred_ai_key_id', sa.String(length=64), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    op.create_table(
        'organization_memberships',
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(length=24), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_membership_org_user'),
    )
    op.create_index(op.f('ix_organization_memberships_organization_id'), 'organization_memberships', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_memberships_user_id'), 'organization_memberships', ['user_id'], unique=False)

    op.create_table(
        'provider_api_keys',
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('created_by_user_id', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('key_name', sa.String(length=96), nullable=False),
        sa.Column('masked_key', sa.String(length=64), nullable=False),
        sa.Column('encrypted_key', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provider_api_keys_created_by_user_id'), 'provider_api_keys', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_provider_api_keys_organization_id'), 'provider_api_keys', ['organization_id'], unique=False)
    op.create_index(op.f('ix_provider_api_keys_provider_name'), 'provider_api_keys', ['provider_name'], unique=False)
    op.create_index(op.f('ix_provider_api_keys_status'), 'provider_api_keys', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_provider_api_keys_status'), table_name='provider_api_keys')
    op.drop_index(op.f('ix_provider_api_keys_provider_name'), table_name='provider_api_keys')
    op.drop_index(op.f('ix_provider_api_keys_organization_id'), table_name='provider_api_keys')
    op.drop_index(op.f('ix_provider_api_keys_created_by_user_id'), table_name='provider_api_keys')
    op.drop_table('provider_api_keys')

    op.drop_index(op.f('ix_organization_memberships_user_id'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_organization_id'), table_name='organization_memberships')
    op.drop_table('organization_memberships')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'email')
