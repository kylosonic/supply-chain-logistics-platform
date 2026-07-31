"""Add Phase 1-3 models

Revision ID: 20260731_0009
Revises: 20260731_0008
Create Date: 2026-07-31 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260731_0009'
down_revision = '20260731_0008'
branch_labels = None
depends_on = None


def upgrade():
    # item temperature_threshold
    op.add_column('items', sa.Column('temperature_threshold', sa.Float(), nullable=True))
    
    # dock_appointments
    op.create_table(
        'dock_appointments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False),
        sa.Column('truck_id', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expected_time', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # freight_invoices
    op.create_table(
        'freight_invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('carrier_id', sa.String(length=128), nullable=False),
        sa.Column('quoted_rate', sa.Float(), nullable=False),
        sa.Column('actual_rate', sa.Float(), nullable=False),
        sa.Column('variance', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['historical_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('freight_invoices')
    op.drop_table('dock_appointments')
    op.drop_column('items', 'temperature_threshold')
