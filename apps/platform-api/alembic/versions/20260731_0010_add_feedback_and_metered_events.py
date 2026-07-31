"""Add feedback and metered event models

Revision ID: 20260731_0010
Revises: 20260731_0009
Create Date: 2026-07-31 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260731_0010'
down_revision = '20260731_0009'
branch_labels = None
depends_on = None


def upgrade():
    # feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_category'), 'feedback', ['category'], unique=False)
    
    # metered_events table
    op.create_table(
        'metered_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metered_events_organization_id'), 'metered_events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_metered_events_event_type'), 'metered_events', ['event_type'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_metered_events_event_type'), table_name='metered_events')
    op.drop_index(op.f('ix_metered_events_organization_id'), table_name='metered_events')
    op.drop_table('metered_events')
    
    op.drop_index(op.f('ix_feedback_category'), table_name='feedback')
    op.drop_table('feedback')
