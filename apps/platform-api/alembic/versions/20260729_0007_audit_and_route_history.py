"""add audit events and route optimization history

Revision ID: 20260729_0007
Revises: 20260727_0006
Create Date: 2026-07-29 00:07:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260729_0007'
down_revision = '20260727_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_events',
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=64), nullable=True),
        sa.Column('actor_user_id', sa.String(), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_events_actor_user_id'), 'audit_events', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_events_entity_id'), 'audit_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_events_entity_type'), 'audit_events', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_events_event_type'), 'audit_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_events_organization_id'), 'audit_events', ['organization_id'], unique=False)

    op.create_table(
        'route_optimization_runs',
        sa.Column('actor_user_id', sa.String(), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('persisted_schedule_id', sa.String(), nullable=True),
        sa.Column('route_name', sa.String(length=128), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('start_warehouse_code', sa.String(length=32), nullable=False),
        sa.Column('vehicle_capacity_units', sa.Integer(), nullable=False),
        sa.Column('max_stops', sa.Integer(), nullable=False),
        sa.Column('speed_kmh', sa.Float(), nullable=False),
        sa.Column('cost_per_km', sa.Float(), nullable=False),
        sa.Column('objective', sa.String(length=32), nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('estimated_duration_min', sa.Integer(), nullable=False),
        sa.Column('capacity_used', sa.Integer(), nullable=False),
        sa.Column('deliveries_count', sa.Integer(), nullable=False),
        sa.Column('stops_count', sa.Integer(), nullable=False),
        sa.Column('unassigned_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('persist_requested', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deliveries_json', sa.JSON(), nullable=False),
        sa.Column('weights_json', sa.JSON(), nullable=False),
        sa.Column('stops_json', sa.JSON(), nullable=False),
        sa.Column('unassigned_deliveries_json', sa.JSON(), nullable=False),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['persisted_schedule_id'], ['route_schedules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_route_optimization_runs_actor_user_id'), 'route_optimization_runs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_route_optimization_runs_organization_id'), 'route_optimization_runs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_route_optimization_runs_persisted_schedule_id'), 'route_optimization_runs', ['persisted_schedule_id'], unique=False)
    op.create_index(op.f('ix_route_optimization_runs_schedule_date'), 'route_optimization_runs', ['schedule_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_route_optimization_runs_schedule_date'), table_name='route_optimization_runs')
    op.drop_index(op.f('ix_route_optimization_runs_persisted_schedule_id'), table_name='route_optimization_runs')
    op.drop_index(op.f('ix_route_optimization_runs_organization_id'), table_name='route_optimization_runs')
    op.drop_index(op.f('ix_route_optimization_runs_actor_user_id'), table_name='route_optimization_runs')
    op.drop_table('route_optimization_runs')

    op.drop_index(op.f('ix_audit_events_organization_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_event_type'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_entity_type'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_entity_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_user_id'), table_name='audit_events')
    op.drop_table('audit_events')