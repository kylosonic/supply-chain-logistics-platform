"""Migrate all UUID columns from VARCHAR to native PostgreSQL UUID type.

Revision ID: 20260803_0012
Revises: 20260802_0011
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op

revision = '20260803_0012'
down_revision = '20260802_0011'
branch_labels = None
depends_on = None

FK_DROPS = [
    ('alerts', 'alerts_acknowledged_by_user_id_fkey'),
    ('alerts', 'alerts_resolved_by_user_id_fkey'),
    ('audit_events', 'audit_events_actor_user_id_fkey'),
    ('audit_events', 'audit_events_organization_id_fkey'),
    ('dock_appointments', 'dock_appointments_warehouse_id_fkey'),
    ('freight_invoices', 'freight_invoices_order_id_fkey'),
    ('inventory', 'inventory_warehouse_id_fkey'),
    ('inventory', 'inventory_item_id_fkey'),
    ('inventory', 'inventory_organization_id_fkey'),
    ('items', 'items_organization_id_fkey'),
    ('organization_memberships', 'organization_memberships_organization_id_fkey'),
    ('organization_memberships', 'organization_memberships_user_id_fkey'),
    ('metered_events', 'metered_events_organization_id_fkey'),
    ('historical_orders', 'historical_orders_warehouse_id_fkey'),
    ('historical_orders', 'historical_orders_item_id_fkey'),
    ('historical_orders', 'historical_orders_organization_id_fkey'),
    ('provider_api_keys', 'provider_api_keys_organization_id_fkey'),
    ('provider_api_keys', 'provider_api_keys_created_by_user_id_fkey'),
    ('replenishment_plans', 'replenishment_plans_warehouse_id_fkey'),
    ('replenishment_plans', 'replenishment_plans_item_id_fkey'),
    ('replenishment_plans', 'replenishment_plans_created_by_user_id_fkey'),
    ('replenishment_plans', 'replenishment_plans_approved_by_user_id_fkey'),
    ('route_schedules', 'route_schedules_start_warehouse_id_fkey'),
    ('route_schedules', 'route_schedules_assigned_asset_id_fkey'),
    ('route_stops', 'route_stops_route_schedule_id_fkey'),
    ('route_stops', 'route_stops_warehouse_id_fkey'),
    ('route_optimization_runs', 'route_optimization_runs_actor_user_id_fkey'),
    ('route_optimization_runs', 'route_optimization_runs_organization_id_fkey'),
    ('route_optimization_runs', 'route_optimization_runs_persisted_schedule_id_fkey'),
    ('shipments', 'shipments_route_schedule_id_fkey'),
    ('shipments', 'shipments_origin_warehouse_id_fkey'),
    ('shipments', 'shipments_destination_warehouse_id_fkey'),
    ('shipments', 'shipments_item_id_fkey'),
    ('organization_usage_counters', 'organization_usage_counters_organization_id_fkey'),
    ('warehouses', 'warehouses_organization_id_fkey'),
]

FK_ADDS = [
    ('alerts', 'acknowledged_by_user_id', 'users', 'id', 'SET NULL'),
    ('alerts', 'resolved_by_user_id', 'users', 'id', 'SET NULL'),
    ('audit_events', 'actor_user_id', 'users', 'id', 'SET NULL'),
    ('audit_events', 'organization_id', 'organizations', 'id', 'SET NULL'),
    ('dock_appointments', 'warehouse_id', 'warehouses', 'id', 'CASCADE'),
    ('freight_invoices', 'order_id', 'historical_orders', 'id', 'CASCADE'),
    ('inventory', 'warehouse_id', 'warehouses', 'id', 'CASCADE'),
    ('inventory', 'item_id', 'items', 'id', 'CASCADE'),
    ('inventory', 'organization_id', 'organizations', 'id', 'SET NULL'),
    ('items', 'organization_id', 'organizations', 'id', 'SET NULL'),
    ('organization_memberships', 'organization_id', 'organizations', 'id', 'CASCADE'),
    ('organization_memberships', 'user_id', 'users', 'id', 'CASCADE'),
    ('metered_events', 'organization_id', 'organizations', 'id', 'CASCADE'),
    ('historical_orders', 'warehouse_id', 'warehouses', 'id', 'CASCADE'),
    ('historical_orders', 'item_id', 'items', 'id', 'CASCADE'),
    ('historical_orders', 'organization_id', 'organizations', 'id', 'SET NULL'),
    ('provider_api_keys', 'organization_id', 'organizations', 'id', 'CASCADE'),
    ('provider_api_keys', 'created_by_user_id', 'users', 'id', 'RESTRICT'),
    ('replenishment_plans', 'warehouse_id', 'warehouses', 'id', 'CASCADE'),
    ('replenishment_plans', 'item_id', 'items', 'id', 'CASCADE'),
    ('replenishment_plans', 'created_by_user_id', 'users', 'id', 'RESTRICT'),
    ('replenishment_plans', 'approved_by_user_id', 'users', 'id', 'SET NULL'),
    ('route_schedules', 'start_warehouse_id', 'warehouses', 'id', 'RESTRICT'),
    ('route_schedules', 'assigned_asset_id', 'fleet_assets', 'id', 'SET NULL'),
    ('route_stops', 'route_schedule_id', 'route_schedules', 'id', 'CASCADE'),
    ('route_stops', 'warehouse_id', 'warehouses', 'id', 'RESTRICT'),
    ('route_optimization_runs', 'actor_user_id', 'users', 'id', 'SET NULL'),
    ('route_optimization_runs', 'organization_id', 'organizations', 'id', 'SET NULL'),
    ('route_optimization_runs', 'persisted_schedule_id', 'route_schedules', 'id', 'SET NULL'),
    ('shipments', 'route_schedule_id', 'route_schedules', 'id', 'SET NULL'),
    ('shipments', 'origin_warehouse_id', 'warehouses', 'id', 'RESTRICT'),
    ('shipments', 'destination_warehouse_id', 'warehouses', 'id', 'RESTRICT'),
    ('shipments', 'item_id', 'items', 'id', 'RESTRICT'),
    ('organization_usage_counters', 'organization_id', 'organizations', 'id', 'CASCADE'),
    ('warehouses', 'organization_id', 'organizations', 'id', 'SET NULL'),
]

ID_TABLES = [
    'alerts', 'audit_events', 'dock_appointments', 'fleet_assets',
    'freight_invoices', 'inventory', 'items', 'organization_memberships',
    'metered_events', 'historical_orders', 'organizations',
    'provider_api_keys', 'replenishment_plans', 'route_schedules',
    'route_stops', 'route_optimization_runs', 'shipments',
    'organization_usage_counters', 'users', 'warehouses',
    'feedback', 'route_history',
]

FK_COLUMNS = [
    ('alerts', 'acknowledged_by_user_id'),
    ('alerts', 'resolved_by_user_id'),
    ('audit_events', 'actor_user_id'),
    ('audit_events', 'organization_id'),
    ('dock_appointments', 'warehouse_id'),
    ('freight_invoices', 'order_id'),
    ('inventory', 'warehouse_id'),
    ('inventory', 'item_id'),
    ('inventory', 'organization_id'),
    ('items', 'organization_id'),
    ('organization_memberships', 'organization_id'),
    ('organization_memberships', 'user_id'),
    ('metered_events', 'organization_id'),
    ('historical_orders', 'warehouse_id'),
    ('historical_orders', 'item_id'),
    ('historical_orders', 'organization_id'),
    ('provider_api_keys', 'organization_id'),
    ('provider_api_keys', 'created_by_user_id'),
    ('replenishment_plans', 'warehouse_id'),
    ('replenishment_plans', 'item_id'),
    ('replenishment_plans', 'created_by_user_id'),
    ('replenishment_plans', 'approved_by_user_id'),
    ('route_schedules', 'start_warehouse_id'),
    ('route_schedules', 'assigned_asset_id'),
    ('route_stops', 'route_schedule_id'),
    ('route_stops', 'warehouse_id'),
    ('route_optimization_runs', 'actor_user_id'),
    ('route_optimization_runs', 'organization_id'),
    ('route_optimization_runs', 'persisted_schedule_id'),
    ('shipments', 'route_schedule_id'),
    ('shipments', 'origin_warehouse_id'),
    ('shipments', 'destination_warehouse_id'),
    ('shipments', 'item_id'),
    ('organization_usage_counters', 'organization_id'),
    ('warehouses', 'organization_id'),
]


def upgrade():
    for table, constraint in FK_DROPS:
        op.drop_constraint(constraint, table, type_='foreignkey')

    for table in ID_TABLES:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN id TYPE uuid USING id::uuid')

    for table, column in FK_COLUMNS:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN {column} TYPE uuid USING {column}::uuid')

    for table, column, ref_table, ref_column, ondelete in FK_ADDS:
        constraint_name = f'{table}_{column}_fkey'
        op.create_foreign_key(constraint_name, table, ref_table, [column], [ref_column], ondelete=ondelete)


def downgrade():
    for table, constraint in FK_DROPS:
        op.drop_constraint(constraint, table, type_='foreignkey')

    for table, column in FK_COLUMNS:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar(36) USING {column}::varchar')

    for table in ID_TABLES:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN id TYPE varchar(36) USING id::varchar')

    for table, column, ref_table, ref_column, ondelete in FK_ADDS:
        constraint_name = f'{table}_{column}_fkey'
        op.create_foreign_key(constraint_name, table, ref_table, [column], [ref_column], ondelete=ondelete)
