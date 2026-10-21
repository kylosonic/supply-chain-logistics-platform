"""Add customer delivery, time-window dispatch, POD, and driver cash flow.

Revision ID: 20260823_0024
Revises: 20260822_0023
Create Date: 2026-10-21 00:00:00.000000
"""

# ruff: noqa: E501

import sqlalchemy as sa

from alembic import op
from app.db.custom_types import UUIDType

revision = '20260823_0024'
down_revision = '20260822_0023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'customers',
        sa.Column('id', UUIDType(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'organization_id',
            UUIDType(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=160), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_customers_org_code'),
    )
    op.create_index('ix_customers_organization_id', 'customers', ['organization_id'])

    op.create_table(
        'dispatch_runs',
        sa.Column('id', UUIDType(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'organization_id',
            UUIDType(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('route_name', sa.String(length=128), nullable=False),
        sa.Column('plan_date', sa.Date(), nullable=False),
        sa.Column('start_label', sa.String(length=160), nullable=False),
        sa.Column('start_latitude', sa.Float(), nullable=False),
        sa.Column('start_longitude', sa.Float(), nullable=False),
        sa.Column('vehicle_capacity_units', sa.Integer(), nullable=False),
        sa.Column('max_stops', sa.Integer(), nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False, server_default='0'),
        sa.Column('estimated_duration_min', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expected_cash_etb', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('stops_json', sa.JSON(), nullable=True),
        sa.Column('unassigned_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='planned'),
        sa.Column('driver_id', UUIDType(), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column(
            'created_by_user_id', UUIDType(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
        ),
        sa.Column('cash_closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_dispatch_runs_organization_id', 'dispatch_runs', ['organization_id'])
    op.create_index('ix_dispatch_runs_plan_date', 'dispatch_runs', ['plan_date'])
    op.create_index('ix_dispatch_runs_driver_id', 'dispatch_runs', ['driver_id'])

    op.create_table(
        'delivery_orders',
        sa.Column('id', UUIDType(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'organization_id',
            UUIDType(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'customer_id', UUIDType(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False
        ),
        sa.Column('item_id', UUIDType(), sa.ForeignKey('items.id', ondelete='SET NULL'), nullable=True),
        sa.Column(
            'dispatch_run_id',
            UUIDType(),
            sa.ForeignKey('dispatch_runs.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('driver_id', UUIDType(), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('order_no', sa.String(length=64), nullable=False),
        sa.Column('quantity_units', sa.Integer(), nullable=False),
        sa.Column('cod_amount_etb', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('service_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('stop_sequence', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='planned'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collected_cash_etb', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('cash_declared_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cash_settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cash_note', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('organization_id', 'order_no', name='uq_delivery_orders_org_order_no'),
    )
    op.create_index('ix_delivery_orders_organization_id', 'delivery_orders', ['organization_id'])
    op.create_index('ix_delivery_orders_customer_id', 'delivery_orders', ['customer_id'])
    op.create_index('ix_delivery_orders_dispatch_run_id', 'delivery_orders', ['dispatch_run_id'])
    op.create_index('ix_delivery_orders_driver_id', 'delivery_orders', ['driver_id'])
    op.create_index('ix_delivery_orders_order_no', 'delivery_orders', ['order_no'])
    op.create_index('ix_delivery_orders_status', 'delivery_orders', ['status'])
    op.create_index(
        'ix_delivery_orders_dispatch_sequence',
        'delivery_orders',
        ['dispatch_run_id', 'stop_sequence'],
    )

    op.create_table(
        'delivery_proofs',
        sa.Column('id', UUIDType(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'organization_id',
            UUIDType(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'delivery_order_id',
            UUIDType(),
            sa.ForeignKey('delivery_orders.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('proof_sequence', sa.Integer(), nullable=False),
        sa.Column('proof_kind', sa.String(length=16), nullable=False, server_default='photo'),
        sa.Column('content_type', sa.String(length=64), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('file_sha256', sa.String(length=64), nullable=False),
        sa.Column('recipient_name', sa.String(length=160), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            'organization_id',
            'delivery_order_id',
            'proof_sequence',
            name='uq_delivery_proofs_order_sequence',
        ),
    )
    op.create_index('ix_delivery_proofs_organization_id', 'delivery_proofs', ['organization_id'])
    op.create_index('ix_delivery_proofs_delivery_order_id', 'delivery_proofs', ['delivery_order_id'])


def downgrade() -> None:
    op.drop_index('ix_delivery_proofs_delivery_order_id', table_name='delivery_proofs')
    op.drop_index('ix_delivery_proofs_organization_id', table_name='delivery_proofs')
    op.drop_table('delivery_proofs')
    op.drop_index('ix_delivery_orders_dispatch_sequence', table_name='delivery_orders')
    op.drop_index('ix_delivery_orders_status', table_name='delivery_orders')
    op.drop_index('ix_delivery_orders_order_no', table_name='delivery_orders')
    op.drop_index('ix_delivery_orders_driver_id', table_name='delivery_orders')
    op.drop_index('ix_delivery_orders_dispatch_run_id', table_name='delivery_orders')
    op.drop_index('ix_delivery_orders_customer_id', table_name='delivery_orders')
    op.drop_index('ix_delivery_orders_organization_id', table_name='delivery_orders')
    op.drop_table('delivery_orders')
    op.drop_index('ix_dispatch_runs_driver_id', table_name='dispatch_runs')
    op.drop_index('ix_dispatch_runs_plan_date', table_name='dispatch_runs')
    op.drop_index('ix_dispatch_runs_organization_id', table_name='dispatch_runs')
    op.drop_table('dispatch_runs')
    op.drop_index('ix_customers_organization_id', table_name='customers')
    op.drop_table('customers')
