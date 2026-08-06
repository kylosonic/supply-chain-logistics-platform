"""Activation Phase 4: data_origin columns, org-scoped business-key
uniqueness, fleet_assets.organization_id, activation state + crossings.

Revision ID: 20260806_0016
Revises: 20260806_0015
Create Date: 2026-08-06 00:00:00.000000

§0A adjudication (blueprint amendment): the legacy GLOBAL unique indexes
on warehouses.code / items.sku / fleet_assets.vehicle_code are replaced
by composite org-scoped unique indexes so per-workspace seeding (decision
#11) and org-scoped upserts (decision #13) can coexist. Plain
CREATE/DROP INDEX in BOTH dialects — no batch table-rebuild — so the
Phase 3 sqlite-quirk precedent (constraint add/drop not viable on sqlite)
does NOT apply here. NULL-org legacy rows stay legal: NULLs are distinct
under unique-index semantics in both Postgres and sqlite.

SQLITE QUIRK (empirically verified on SQLAlchemy 2.0.36 / alembic 1.14.1):
constraint add/drop is NOT viable on sqlite, so the data_origin CHECK
constraints and the fleet_assets FK below are Postgres-only. sqlite runs
get the columns, indexes, and the two new tables only; the model
CheckConstraints are authoritative for test databases, which build via
``Base.metadata.create_all`` (Phase 2/3 precedent).
"""
import sqlalchemy as sa
from alembic import op

revision = '20260806_0016'
down_revision = '20260806_0015'
branch_labels = None
depends_on = None

_DATA_TABLES = ('warehouses', 'items', 'fleet_assets', 'inventory', 'historical_orders')


def _add_data_origin_columns() -> None:
    for table in _DATA_TABLES:
        op.add_column(
            table,
            sa.Column('data_origin', sa.String(length=8), server_default='real', nullable=False),
        )


def _add_data_origin_checks() -> None:
    for table in _DATA_TABLES:
        op.create_check_constraint(
            f'ck_{table}_data_origin',
            table,
            "data_origin IN ('sample','real')",
        )


def _drop_data_origin_checks() -> None:
    for table in _DATA_TABLES:
        op.drop_constraint(f'ck_{table}_data_origin', table, type_='check')


def _drop_data_origin_columns() -> None:
    for table in _DATA_TABLES:
        op.drop_column(table, 'data_origin')


def _replace_global_unique_indexes() -> None:
    """Global-unique -> composite org-scoped unique (both dialects, §0A)."""
    op.drop_index('ix_warehouses_code', table_name='warehouses')
    op.create_index(
        'ix_warehouses_org_code',
        'warehouses',
        ['organization_id', 'code'],
        unique=True,
    )
    op.drop_index('ix_items_sku', table_name='items')
    op.create_index(
        'ix_items_org_sku',
        'items',
        ['organization_id', 'sku'],
        unique=True,
    )
    op.drop_index('ix_fleet_assets_vehicle_code', table_name='fleet_assets')
    op.create_index(
        'ix_fleet_assets_org_vehicle_code',
        'fleet_assets',
        ['organization_id', 'vehicle_code'],
        unique=True,
    )


def _restore_global_unique_indexes() -> None:
    op.drop_index('ix_warehouses_org_code', table_name='warehouses')
    op.create_index('ix_warehouses_code', 'warehouses', ['code'], unique=True)
    op.drop_index('ix_items_org_sku', table_name='items')
    op.create_index('ix_items_sku', 'items', ['sku'], unique=True)
    op.drop_index('ix_fleet_assets_org_vehicle_code', table_name='fleet_assets')
    op.create_index('ix_fleet_assets_vehicle_code', 'fleet_assets', ['vehicle_code'], unique=True)


def _fleet_organization_id() -> None:
    op.add_column(
        'fleet_assets',
        sa.Column('organization_id', sa.CHAR(length=36), nullable=True),
    )
    op.create_index('ix_fleet_assets_organization_id', 'fleet_assets', ['organization_id'], unique=False)


def _fleet_organization_id_postgres() -> None:
    op.create_foreign_key(
        'fk_fleet_assets_organization',
        'fleet_assets',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL',
    )


def _create_activation_state_table() -> None:
    op.create_table(
        'organization_activation_state',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('m6_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('toast_fired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('seeded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', name='uq_activation_state_org'),
    )
    op.create_index(
        'ix_activation_state_organization_id', 'organization_activation_state', ['organization_id']
    )


def _create_threshold_crossings_table() -> None:
    op.create_table(
        'threshold_crossings',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('threshold_level', sa.String(length=8), nullable=False),
        sa.Column('fired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'organization_id',
            'period_start',
            'threshold_level',
            name='uq_threshold_crossing_org_period_level',
        ),
    )
    op.create_index('ix_threshold_crossings_organization_id', 'threshold_crossings', ['organization_id'])


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    _add_data_origin_columns()
    if not is_sqlite:
        _add_data_origin_checks()
    _fleet_organization_id()
    if not is_sqlite:
        _fleet_organization_id_postgres()
    _replace_global_unique_indexes()
    _create_activation_state_table()
    _create_threshold_crossings_table()


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    op.drop_index('ix_threshold_crossings_organization_id', table_name='threshold_crossings')
    op.drop_table('threshold_crossings')
    op.drop_index('ix_activation_state_organization_id', table_name='organization_activation_state')
    op.drop_table('organization_activation_state')
    _restore_global_unique_indexes()
    if not is_sqlite:
        op.drop_constraint('fk_fleet_assets_organization', 'fleet_assets', type_='foreignkey')
    op.drop_index('ix_fleet_assets_organization_id', table_name='fleet_assets')
    op.drop_column('fleet_assets', 'organization_id')
    if not is_sqlite:
        _drop_data_origin_checks()
    _drop_data_origin_columns()
