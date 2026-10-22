"""Quarantine rows whose organization cannot be attributed.

Revision ID: 20260821_0022
Revises: 20260813_0021
Create Date: 2026-10-21 00:00:00.000000

The old single-tenant dataset contained rows with ``organization_id = NULL``.
Those rows cannot be safely assigned to a customer workspace by inference.
This migration preserves them under an inactive, memberless quarantine
organization so no tenant read path can mistake them for its own data.

Downgrade restores the NULL attribution and removes the quarantine organization.
"""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from alembic import op
from app.db.custom_types import UUIDType

revision = '20260821_0022'
down_revision = '20260813_0021'
branch_labels = None
depends_on = None

QUARANTINE_ORG_ID = UUID('00000000-0000-4000-8000-000000000022')
QUARANTINE_SLUG = 'legacy-unassigned-data'

_ORGANIZATIONS = sa.table(
    'organizations',
    sa.column('id', UUIDType),
    sa.column('name', sa.String),
    sa.column('slug', sa.String),
    sa.column('primary_email_domain', sa.String),
    sa.column('subscription_tier', sa.String),
    sa.column('subscription_status', sa.String),
    sa.column('billing_phase', sa.String),
    sa.column('is_active', sa.Boolean),
)


def _scoped_tables(bind: sa.engine.Connection) -> list[str]:
    inspector = sa.inspect(bind)
    tables: list[str] = []
    for name in inspector.get_table_names():
        columns = {column['name'] for column in inspector.get_columns(name)}
        if 'organization_id' in columns:
            tables.append(name)
    return sorted(tables)


def _quarantine_id(bind: sa.engine.Connection) -> UUID | None:
    row = bind.execute(
        sa.text(
            'SELECT id, slug, name, is_active FROM organizations '
            'WHERE id = :quarantine_id OR slug = :slug'
        ),
        {'quarantine_id': QUARANTINE_ORG_ID, 'slug': QUARANTINE_SLUG},
    ).first()
    if row is None:
        return None
    resolved_id = row[0] if isinstance(row[0], UUID) else UUID(str(row[0]))
    if (
        resolved_id != QUARANTINE_ORG_ID
        or row[1] != QUARANTINE_SLUG
        or row[2] != 'Legacy unassigned data'
        or bool(row[3])
    ):
        raise RuntimeError(
            'Quarantine organization identity conflict: refusing to move or delete tenant data'
        )
    return resolved_id


def upgrade() -> None:
    bind = op.get_bind()
    tables = _scoped_tables(bind)
    has_legacy_rows = any(
        bind.execute(sa.text(f'SELECT 1 FROM "{table}" WHERE organization_id IS NULL LIMIT 1')).first()
        is not None
        for table in tables
    )
    if not has_legacy_rows:
        return

    quarantine_id = _quarantine_id(bind)
    if quarantine_id is None:
        bind.execute(
            _ORGANIZATIONS.insert().values(
                id=QUARANTINE_ORG_ID,
                name='Legacy unassigned data',
                slug=QUARANTINE_SLUG,
                primary_email_domain=None,
                subscription_tier='free',
                subscription_status='active',
                billing_phase='free',
                is_active=False,
            )
        )
        quarantine_id = QUARANTINE_ORG_ID

    for table in tables:
        scoped = sa.table(table, sa.column('organization_id', UUIDType))
        bind.execute(
            scoped.update().where(scoped.c.organization_id.is_(None)).values(organization_id=quarantine_id)
        )


def downgrade() -> None:
    bind = op.get_bind()
    quarantine_id = _quarantine_id(bind)
    if quarantine_id is None:
        return
    inspector = sa.inspect(bind)
    if 'organization_memberships' in inspector.get_table_names():
        member_count = bind.execute(
            sa.text(
                'SELECT COUNT(*) FROM organization_memberships '
                'WHERE organization_id = :quarantine_id'
            ),
            {'quarantine_id': QUARANTINE_ORG_ID},
        ).scalar_one()
        if member_count:
            raise RuntimeError(
                'Quarantine organization has members; refusing destructive downgrade'
            )
    if 'members' in inspector.get_table_names():
        member_count = bind.execute(
            sa.text('SELECT COUNT(*) FROM members WHERE organization_id = :quarantine_id'),
            {'quarantine_id': QUARANTINE_ORG_ID},
        ).scalar_one()
        if member_count:
            raise RuntimeError(
                'Quarantine organization has members; refusing destructive downgrade'
            )

    for table in _scoped_tables(bind):
        scoped = sa.table(table, sa.column('organization_id', UUIDType))
        bind.execute(
            scoped.update().where(scoped.c.organization_id == quarantine_id).values(organization_id=None)
        )

    bind.execute(
        sa.text('DELETE FROM organizations WHERE id = :quarantine_id'),
        {'quarantine_id': QUARANTINE_ORG_ID},
    )
