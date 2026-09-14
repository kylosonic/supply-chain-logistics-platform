"""NB-64 (audit H-1) — tenant scoping for operational surfaces.

Revision ID: 20260811_0019
Revises: 20260808_0018
Create Date: 2026-08-11 00:00:00.000000

Adds ``organization_id`` to the six tables whose endpoints guarded only by a
*global* role and therefore returned every tenant's rows:

- ``shipments``
- ``alerts``
- ``replenishment_plans``
- ``route_schedules`` (``route_stops`` is reached only through its schedule)
- ``dock_appointments``
- ``freight_invoices``

Columns are nullable-additive (mirroring 0011) so the migration is safe on a
live database, then **backfilled** from the natural parent chain:

- shipment -> ``origin_warehouse_id`` -> ``warehouses.organization_id``
- alert -> ``related_entity_id`` (shipment uuid / ``warehouse:sku``) -> org
- replenishment_plan / dock_appointment / route_schedule -> warehouse org
- freight_invoice -> ``order_id`` -> ``historical_orders.organization_id``

Rows whose parent carries no organization keep NULL, which the API treats as
"legacy, visible to any org" (``include_legacy_null`` in
``app/api/security.py``) — identical to the TECH-58 contract for warehouses
and items.

Dialect note: FK creation is skipped on sqlite, where batch DDL for added
foreign keys is malformed (documented precedent in 0015/0018); models stay
authoritative on the sqlite test path.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = '20260811_0019'
down_revision = '20260808_0018'
branch_labels = None
depends_on = None


# (table, backfill SQL for Postgres, backfill SQL for sqlite)
_BACKFILLS: list[tuple[str, str, str]] = [
    (
        'shipments',
        """
        UPDATE shipments AS s
           SET organization_id = w.organization_id
          FROM warehouses AS w
         WHERE s.origin_warehouse_id = w.id
           AND s.organization_id IS NULL
           AND w.organization_id IS NOT NULL
        """,
        """
        UPDATE shipments
           SET organization_id = (
               SELECT w.organization_id FROM warehouses AS w
                WHERE w.id = shipments.origin_warehouse_id
           )
         WHERE organization_id IS NULL
           AND origin_warehouse_id IS NOT NULL
           AND (SELECT w.organization_id FROM warehouses AS w
                 WHERE w.id = shipments.origin_warehouse_id) IS NOT NULL
        """,
    ),
    (
        'replenishment_plans',
        """
        UPDATE replenishment_plans AS p
           SET organization_id = w.organization_id
          FROM warehouses AS w
         WHERE p.warehouse_id = w.id
           AND p.organization_id IS NULL
           AND w.organization_id IS NOT NULL
        """,
        """
        UPDATE replenishment_plans
           SET organization_id = (
               SELECT w.organization_id FROM warehouses AS w
                WHERE w.id = replenishment_plans.warehouse_id
           )
         WHERE organization_id IS NULL
           AND warehouse_id IS NOT NULL
           AND (SELECT w.organization_id FROM warehouses AS w
                 WHERE w.id = replenishment_plans.warehouse_id) IS NOT NULL
        """,
    ),
    (
        'route_schedules',
        """
        UPDATE route_schedules AS r
           SET organization_id = w.organization_id
          FROM warehouses AS w
         WHERE r.start_warehouse_id = w.id
           AND r.organization_id IS NULL
           AND w.organization_id IS NOT NULL
        """,
        """
        UPDATE route_schedules
           SET organization_id = (
               SELECT w.organization_id FROM warehouses AS w
                WHERE w.id = route_schedules.start_warehouse_id
           )
         WHERE organization_id IS NULL
           AND start_warehouse_id IS NOT NULL
           AND (SELECT w.organization_id FROM warehouses AS w
                 WHERE w.id = route_schedules.start_warehouse_id) IS NOT NULL
        """,
    ),
    (
        'dock_appointments',
        """
        UPDATE dock_appointments AS d
           SET organization_id = w.organization_id
          FROM warehouses AS w
         WHERE d.warehouse_id = w.id
           AND d.organization_id IS NULL
           AND w.organization_id IS NOT NULL
        """,
        """
        UPDATE dock_appointments
           SET organization_id = (
               SELECT w.organization_id FROM warehouses AS w
                WHERE w.id = dock_appointments.warehouse_id
           )
         WHERE organization_id IS NULL
           AND warehouse_id IS NOT NULL
           AND (SELECT w.organization_id FROM warehouses AS w
                 WHERE w.id = dock_appointments.warehouse_id) IS NOT NULL
        """,
    ),
    (
        'freight_invoices',
        """
        UPDATE freight_invoices AS f
           SET organization_id = o.organization_id
          FROM historical_orders AS o
         WHERE f.order_id = o.id
           AND f.organization_id IS NULL
           AND o.organization_id IS NOT NULL
        """,
        """
        UPDATE freight_invoices
           SET organization_id = (
               SELECT o.organization_id FROM historical_orders AS o
                WHERE o.id = freight_invoices.order_id
           )
         WHERE organization_id IS NULL
           AND order_id IS NOT NULL
           AND (SELECT o.organization_id FROM historical_orders AS o
                 WHERE o.id = freight_invoices.order_id) IS NOT NULL
        """,
    ),
    (
        'alerts',
        # ``alerts.related_entity_id`` is varchar while ``shipments.id`` is a
        # native uuid on Postgres, so compare on a hyphen-stripped text form of
        # both sides (the same normalisation the API applies when it stores the
        # id as a string).
        """
        UPDATE alerts AS a
           SET organization_id = s.organization_id
          FROM shipments AS s
         WHERE a.related_entity_type = 'shipment'
           AND replace(a.related_entity_id, '-', '') = replace(s.id::text, '-', '')
           AND a.organization_id IS NULL
           AND s.organization_id IS NOT NULL
        """,
        """
        UPDATE alerts
           SET organization_id = (
               SELECT s.organization_id FROM shipments AS s
                WHERE s.id = alerts.related_entity_id
           )
         WHERE organization_id IS NULL
           AND related_entity_type = 'shipment'
           AND related_entity_id IS NOT NULL
           AND (SELECT s.organization_id FROM shipments AS s
                 WHERE s.id = alerts.related_entity_id) IS NOT NULL
        """,
    ),
]


def _add_column(table: str) -> None:
    bind = op.get_bind()
    columns = {column['name'] for column in sa.inspect(bind).get_columns(table)}
    if 'organization_id' in columns:
        return
    op.add_column(table, sa.Column('organization_id', sa.Uuid(), nullable=True))
    op.create_index(f'ix_{table}_organization_id', table, ['organization_id'], unique=False)
    if bind.dialect.name != 'sqlite':
        op.create_foreign_key(
            f'fk_{table}_organization_id_organizations',
            table,
            'organizations',
            ['organization_id'],
            ['id'],
            ondelete='SET NULL',
        )


def _repair_shipment_number_uniqueness() -> None:
    """TECH-49: ``shipment_no`` was globally unique (migration 0003), so two
    tenants could never use the same shipment number — a multi-tenant hazard of
    the same class as the org-scoping rules this revision implements, and now
    reachable because shipment creation accepts a user-supplied number.

    Replace the global unique index with **two partial** unique indexes:

    - ``(organization_id, shipment_no)`` where ``organization_id IS NOT NULL``
    - ``(shipment_no)`` where ``organization_id IS NULL``

    Partial indexes are used rather than one plain composite index because SQL
    treats NULLs as distinct: a composite UNIQUE over a nullable column would
    stop constraining unattributed legacy rows at all. The invariant becomes
    "a shipment number is unique within its tenant, and unattributed rows stay
    globally unique".
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'shipments' not in set(inspector.get_table_names()):
        return

    existing = {index['name'] for index in inspector.get_indexes('shipments')}
    if 'ix_shipments_shipment_no' in existing:
        op.drop_index('ix_shipments_shipment_no', table_name='shipments')

    # Non-unique index for the plain ``shipment_no`` lookup helper.
    if 'ix_shipments_shipment_no_lookup' not in existing:
        op.create_index(
            'ix_shipments_shipment_no_lookup', 'shipments', ['shipment_no'], unique=False
        )

    if 'uq_shipments_org_shipment_no' not in existing:
        op.create_index(
            'uq_shipments_org_shipment_no',
            'shipments',
            ['organization_id', 'shipment_no'],
            unique=True,
            postgresql_where=sa.text('organization_id IS NOT NULL'),
            sqlite_where=sa.text('organization_id IS NOT NULL'),
        )

    if 'uq_shipments_unattributed_shipment_no' not in existing:
        op.create_index(
            'uq_shipments_unattributed_shipment_no',
            'shipments',
            ['shipment_no'],
            unique=True,
            postgresql_where=sa.text('organization_id IS NULL'),
            sqlite_where=sa.text('organization_id IS NULL'),
        )


def upgrade() -> None:
    bind = op.get_bind()

    for table, _, _ in _BACKFILLS:
        _add_column(table)

    # Backfill only runs when the parent tables exist (fresh installs build the
    # schema in order, so they do).
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    for table, pg_sql, sqlite_sql in _BACKFILLS:
        if table not in existing:
            continue
        sql = sqlite_sql if bind.dialect.name == 'sqlite' else pg_sql
        bind.execute(sa.text(sql))

    _repair_shipment_number_uniqueness()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'shipments' in set(inspector.get_table_names()):
        existing = {index['name'] for index in inspector.get_indexes('shipments')}
        for index_name in (
            'uq_shipments_unattributed_shipment_no',
            'uq_shipments_org_shipment_no',
        ):
            if index_name in existing:
                op.drop_index(index_name, table_name='shipments')
        if 'ix_shipments_shipment_no_lookup' in existing:
            op.drop_index('ix_shipments_shipment_no_lookup', table_name='shipments')
        op.create_index('ix_shipments_shipment_no', 'shipments', ['shipment_no'], unique=True)

    for table, _, _ in _BACKFILLS:
        columns = {column['name'] for column in sa.inspect(bind).get_columns(table)}
        if 'organization_id' not in columns:
            continue
        if bind.dialect.name != 'sqlite':
            op.drop_constraint(
                f'fk_{table}_organization_id_organizations', table, type_='foreignkey'
            )
        op.drop_index(f'ix_{table}_organization_id', table_name=table)
        op.drop_column(table, 'organization_id')
