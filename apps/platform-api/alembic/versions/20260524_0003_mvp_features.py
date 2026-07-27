"""add shipments alerts and replenishment plans

Revision ID: 20260524_0003
Revises: 20260518_0002
Create Date: 2026-05-24 00:03:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260524_0003'
down_revision = '20260518_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('alert_type', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column('related_entity_type', sa.String(length=64), nullable=True),
        sa.Column('related_entity_id', sa.String(length=64), nullable=True),
        sa.Column('acknowledged_by_user_id', sa.String(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['acknowledged_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_alerts_alert_type'), 'alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_alerts_related_entity_id'), 'alerts', ['related_entity_id'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)

    op.create_table(
        'replenishment_plans',
        sa.Column('warehouse_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('horizon_weeks', sa.Integer(), nullable=False),
        sa.Column('avg_weekly_demand', sa.Float(), nullable=False),
        sa.Column('suggested_quantity', sa.Integer(), nullable=False),
        sa.Column('approved_quantity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('rationale', sa.String(length=255), nullable=False),
        sa.Column('created_by_user_id', sa.String(), nullable=False),
        sa.Column('approved_by_user_id', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_replenishment_plans_item_id'), 'replenishment_plans', ['item_id'], unique=False)
    op.create_index(op.f('ix_replenishment_plans_status'), 'replenishment_plans', ['status'], unique=False)
    op.create_index(op.f('ix_replenishment_plans_warehouse_id'), 'replenishment_plans', ['warehouse_id'], unique=False)

    op.create_table(
        'shipments',
        sa.Column('shipment_no', sa.String(length=64), nullable=False),
        sa.Column('route_schedule_id', sa.String(), nullable=True),
        sa.Column('origin_warehouse_id', sa.String(), nullable=False),
        sa.Column('destination_warehouse_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('quantity_units', sa.Integer(), nullable=False),
        sa.Column('planned_departure', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('last_known_location', sa.String(length=128), nullable=True),
        sa.Column('delay_reason', sa.String(length=255), nullable=True),
        sa.Column('proof_of_delivery_ref', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['destination_warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['origin_warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['route_schedule_id'], ['route_schedules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shipments_destination_warehouse_id'), 'shipments', ['destination_warehouse_id'], unique=False)
    op.create_index(op.f('ix_shipments_item_id'), 'shipments', ['item_id'], unique=False)
    op.create_index(op.f('ix_shipments_origin_warehouse_id'), 'shipments', ['origin_warehouse_id'], unique=False)
    op.create_index(op.f('ix_shipments_shipment_no'), 'shipments', ['shipment_no'], unique=True)
    op.create_index(op.f('ix_shipments_status'), 'shipments', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_shipments_status'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_shipment_no'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_origin_warehouse_id'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_item_id'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_destination_warehouse_id'), table_name='shipments')
    op.drop_table('shipments')

    op.drop_index(op.f('ix_replenishment_plans_warehouse_id'), table_name='replenishment_plans')
    op.drop_index(op.f('ix_replenishment_plans_status'), table_name='replenishment_plans')
    op.drop_index(op.f('ix_replenishment_plans_item_id'), table_name='replenishment_plans')
    op.drop_table('replenishment_plans')

    op.drop_index(op.f('ix_alerts_status'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_related_entity_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_alert_type'), table_name='alerts')
    op.drop_table('alerts')
