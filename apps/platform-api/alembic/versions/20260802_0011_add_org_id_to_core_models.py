"""Add organization_id to warehouses, items, historical_orders, inventory

Revision ID: 20260802_0011
Revises: 20260731_0010
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '20260802_0011'
down_revision = '20260731_0010'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('warehouses', sa.Column('organization_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_warehouses_organization_id'), 'warehouses', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'warehouses', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')

    op.add_column('items', sa.Column('organization_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_items_organization_id'), 'items', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'items', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')

    op.add_column('historical_orders', sa.Column('organization_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_historical_orders_organization_id'), 'historical_orders', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'historical_orders', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')

    op.add_column('inventory', sa.Column('organization_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_inventory_organization_id'), 'inventory', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'inventory', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint(None, 'inventory', type_='foreignkey')
    op.drop_index(op.f('ix_inventory_organization_id'), table_name='inventory')
    op.drop_column('inventory', 'organization_id')

    op.drop_constraint(None, 'historical_orders', type_='foreignkey')
    op.drop_index(op.f('ix_historical_orders_organization_id'), table_name='historical_orders')
    op.drop_column('historical_orders', 'organization_id')

    op.drop_constraint(None, 'items', type_='foreignkey')
    op.drop_index(op.f('ix_items_organization_id'), table_name='items')
    op.drop_column('items', 'organization_id')

    op.drop_constraint(None, 'warehouses', type_='foreignkey')
    op.drop_index(op.f('ix_warehouses_organization_id'), table_name='warehouses')
    op.drop_column('warehouses', 'organization_id')
