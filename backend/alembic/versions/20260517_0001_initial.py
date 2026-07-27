"""initial schema

Revision ID: 20260517_0001
Revises: 
Create Date: 2026-05-17 00:00:01.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260517_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'items',
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('unit_cost', sa.Float(), nullable=False),
        sa.Column('reorder_level', sa.Integer(), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_items_sku'), 'items', ['sku'], unique=True)

    op.create_table(
        'warehouses',
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=64), nullable=False),
        sa.Column('state', sa.String(length=64), nullable=False),
        sa.Column('country', sa.String(length=64), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('capacity_units', sa.Integer(), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_warehouses_code'), 'warehouses', ['code'], unique=True)

    op.create_table(
        'inventory',
        sa.Column('warehouse_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False),
        sa.Column('safety_stock', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('warehouse_id', 'item_id', name='uq_inventory_warehouse_item'),
    )
    op.create_index(op.f('ix_inventory_item_id'), 'inventory', ['item_id'], unique=False)
    op.create_index(op.f('ix_inventory_warehouse_id'), 'inventory', ['warehouse_id'], unique=False)

    op.create_table(
        'historical_orders',
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('warehouse_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('customer_region', sa.String(length=64), nullable=False),
        sa.Column('weather_avg_temp_c', sa.Float(), nullable=True),
        sa.Column('weather_precip_mm', sa.Float(), nullable=True),
        sa.Column('weather_disruption_index', sa.Float(), nullable=True),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historical_orders_item_id'), 'historical_orders', ['item_id'], unique=False)
    op.create_index(op.f('ix_historical_orders_order_date'), 'historical_orders', ['order_date'], unique=False)
    op.create_index(op.f('ix_historical_orders_warehouse_id'), 'historical_orders', ['warehouse_id'], unique=False)

    op.create_table(
        'route_schedules',
        sa.Column('route_name', sa.String(length=128), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('start_warehouse_id', sa.String(), nullable=False),
        sa.Column('vehicle_capacity_units', sa.Integer(), nullable=False),
        sa.Column('objective', sa.String(length=32), nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('estimated_duration_min', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['start_warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_route_schedules_schedule_date'), 'route_schedules', ['schedule_date'], unique=False)

    op.create_table(
        'route_stops',
        sa.Column('route_schedule_id', sa.String(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.String(), nullable=False),
        sa.Column('planned_arrival', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_departure', sa.DateTime(timezone=True), nullable=True),
        sa.Column('load_units', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['route_schedule_id'], ['route_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_route_stops_route_schedule_id'), 'route_stops', ['route_schedule_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_route_stops_route_schedule_id'), table_name='route_stops')
    op.drop_table('route_stops')

    op.drop_index(op.f('ix_route_schedules_schedule_date'), table_name='route_schedules')
    op.drop_table('route_schedules')

    op.drop_index(op.f('ix_historical_orders_warehouse_id'), table_name='historical_orders')
    op.drop_index(op.f('ix_historical_orders_order_date'), table_name='historical_orders')
    op.drop_index(op.f('ix_historical_orders_item_id'), table_name='historical_orders')
    op.drop_table('historical_orders')

    op.drop_index(op.f('ix_inventory_warehouse_id'), table_name='inventory')
    op.drop_index(op.f('ix_inventory_item_id'), table_name='inventory')
    op.drop_table('inventory')

    op.drop_index(op.f('ix_warehouses_code'), table_name='warehouses')
    op.drop_table('warehouses')

    op.drop_index(op.f('ix_items_sku'), table_name='items')
    op.drop_table('items')
