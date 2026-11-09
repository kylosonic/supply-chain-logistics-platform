"""NB-86 — driver roster and cash-on-delivery reconciliation.

Revision ID: 20260812_0020
Revises: 20260811_0019
Create Date: 2026-08-12 00:00:00.000000

Two operational gaps found by evaluating the product as a buyer would
(see ``docs/behaviors/driver-and-cod-reconciliation.md``):

1. **No driver.** The API had no ``driver`` concept at all. Work was assigned to
   a warehouse and a route, never to a person, so "who is carrying this" lived in
   a phone call and a notebook — the exact failure the product exists to remove.

2. **No cash-on-delivery ledger.** The platform reconciled *bank transfers*
   against invoices, but in this market a driver also collects cash at the door.
   Nothing recorded how much was expected, how much was handed over at the end of
   the day, or what was missing. That is the largest unmonitored cash risk an
   operator carries, and it was invisible to the software.

Additions, all nullable-additive so they are safe on a live database:

- ``drivers`` — roster, tenant-scoped, phone unique per organisation.
- ``shipments.driver_id`` — assignment, ``SET NULL`` on driver deletion so
  cleaning up a roster can never delete delivery history.
- ``shipments.cod_amount_etb`` — cash expected at the door for this shipment.
- ``shipments.client_ref`` — caller-supplied idempotency key (TECH-105), so a
  confirmation replayed over a flaky mobile connection cannot double-count cash.
- ``cash_collections`` — one row per shipment holding COD, carrying expected,
  collected, shortfall, settlement status and the audit chain.

No data movement is required: ``shipments.actual_delivery`` already stores the
delivery timestamp, and ``cash_collections`` starts empty because no historic
cash figure was ever captured. Existing shipments take ``cod_amount_etb = 0``,
which the API reads as "no cash due" (mirrors the ``amount_etb`` semantics in
``wallet_credits``).

Dialect note: migrations execute against Postgres only — the test suite builds
its schema from the models via ``Base.metadata.create_all`` on in-memory sqlite
(``tests/conftest.py``), and sqlite cannot add foreign keys to an existing table
in any case (precedent: 0015/0018/0019). Types therefore follow 0015's
Postgres path.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = '20260812_0020'
down_revision = '20260811_0019'
branch_labels = None
depends_on = None


def _create_drivers_table() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)

    op.create_table(
        'drivers',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('organization_id', uuid_type, nullable=False),
        sa.Column('full_name', sa.String(length=160), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('license_no', sa.String(length=64), nullable=True),
        sa.Column('vehicle_plate', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'phone', name='uq_drivers_org_phone'),
        sa.CheckConstraint("status IN ('active','inactive')", name='ck_drivers_status'),
    )
    op.create_index('ix_drivers_organization_id', 'drivers', ['organization_id'])
    op.create_index('ix_drivers_org_status', 'drivers', ['organization_id', 'status'])


def _add_shipment_columns() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)

    op.add_column('shipments', sa.Column('driver_id', uuid_type, nullable=True))
    op.create_foreign_key(
        'fk_shipments_driver_id_drivers',
        'shipments',
        'drivers',
        ['driver_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_shipments_driver_id', 'shipments', ['driver_id'])

    op.add_column(
        'shipments',
        sa.Column('cod_amount_etb', sa.Numeric(precision=14, scale=2), server_default='0', nullable=False),
    )

    op.add_column('shipments', sa.Column('client_ref', sa.String(length=80), nullable=True))
    # Partial unique index: many rows may hold NULL (nothing to correlate), but a
    # given client reference may resolve only once per tenant. Mirrors the
    # shipments.shipment_no treatment from 0019.
    op.create_index(
        'uq_shipments_org_client_ref',
        'shipments',
        ['organization_id', 'client_ref'],
        unique=True,
        postgresql_where=sa.text('client_ref IS NOT NULL'),
    )


def _create_cash_collections_table() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)

    op.create_table(
        'cash_collections',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('organization_id', uuid_type, nullable=False),
        sa.Column('shipment_id', uuid_type, nullable=False),
        sa.Column('driver_id', uuid_type, nullable=True),
        sa.Column('expected_etb', sa.Numeric(precision=14, scale=2), server_default='0', nullable=False),
        sa.Column('collected_etb', sa.Numeric(precision=14, scale=2), server_default='0', nullable=False),
        sa.Column('shortfall_etb', sa.Numeric(precision=14, scale=2), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=16), server_default='outstanding', nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settled_by_id', uuid_type, nullable=True),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['settled_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        # One cash record per shipment: a replayed delivery confirmation must
        # update the existing row, never open a second one.
        sa.UniqueConstraint('shipment_id', name='uq_cash_collections_shipment'),
        sa.CheckConstraint('expected_etb >= 0', name='ck_cash_collections_expected_non_negative'),
        sa.CheckConstraint('collected_etb >= 0', name='ck_cash_collections_collected_non_negative'),
        sa.CheckConstraint('shortfall_etb >= 0', name='ck_cash_collections_shortfall_non_negative'),
        sa.CheckConstraint(
            "status IN ('outstanding','collected','settled','voided')",
            name='ck_cash_collections_status',
        ),
    )
    op.create_index('ix_cash_collections_organization_id', 'cash_collections', ['organization_id'])
    op.create_index('ix_cash_collections_shipment_id', 'cash_collections', ['shipment_id'])
    op.create_index('ix_cash_collections_driver_id', 'cash_collections', ['driver_id'])
    op.create_index('ix_cash_collections_org_status', 'cash_collections', ['organization_id', 'status'])


def upgrade() -> None:
    _create_drivers_table()
    _add_shipment_columns()
    _create_cash_collections_table()


def downgrade() -> None:
    op.drop_table('cash_collections')

    op.drop_index('uq_shipments_org_client_ref', table_name='shipments')
    op.drop_column('shipments', 'client_ref')
    op.drop_column('shipments', 'cod_amount_etb')
    op.drop_index('ix_shipments_driver_id', table_name='shipments')
    op.drop_constraint('fk_shipments_driver_id_drivers', 'shipments', type_='foreignkey')
    op.drop_column('shipments', 'driver_id')

    op.drop_table('drivers')
