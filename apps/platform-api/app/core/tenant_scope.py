"""NB-64 (audit H-1) — tenant scoping primitives.

Every operator surface must be scoped to the caller's organization. These
helpers are the single shared implementation of that rule so a new endpoint
cannot quietly reintroduce a global query, and so repositories can apply the
same filter without importing the FastAPI dependency layer.

This module deliberately depends only on ``app.db`` / ``app.schemas`` so it can
be imported from anywhere (``app.api.security`` re-exports it for endpoint use);
importing ``app.repositories`` here would recreate the import cycle that
``repositories/routes.py`` -> ``api.security`` -> ``repositories`` would form.

Contract preserved from TECH-58: an actor with **no** organization (legacy
org-less accounts, seeded demo users) keeps the unfiltered pass-through
behaviour, so pre-existing single-tenant flows and their tests are unchanged.
Only org-scoped actors gain the filter.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, or_
from sqlalchemy.orm import Session

from app.models.user import User

__all__ = [
    'actor_organization_id',
    'order_by_organization_first',
    'organization_scoped_get',
    'resolve_scoped_organization',
    'scoped_to_organization',
]


def actor_organization_id(actor: User | None, db: Session) -> UUID | None:
    """Resolve the caller's organization id, or ``None`` for org-less actors.

    Mirrors ``app.services.audit.resolve_actor_organization_id`` but returns a
    real ``UUID`` (not a string) so it can be compared directly against
    ``UUIDType`` columns.
    """
    if actor is None:
        return None

    from app.repositories import MembershipRepository

    raw = MembershipRepository(db).get_organization_id_for_user(actor.id)
    if raw is None:
        return None
    return raw if isinstance(raw, UUID) else UUID(str(raw))


def scoped_to_organization(
    query: Select,
    model: type,
    organization_id: UUID | None,
    *,
    include_legacy_null: bool = True,
) -> Select:
    """Restrict ``query`` over ``model`` to ``organization_id``.

    ``include_legacy_null=True`` (the default for read paths) also matches rows
    whose ``organization_id`` is NULL — they predate org scoping and belong to
    the same single-tenant deployment (TECH-58 semantics). Write paths pass
    ``False`` so an org-scoped actor can never mutate an unattributed row.
    """
    if organization_id is None:
        return query
    if include_legacy_null:
        return query.where(
            or_(
                model.organization_id == organization_id,
                model.organization_id.is_(None),
            )
        )
    return query.where(model.organization_id == organization_id)


def order_by_organization_first(query: Select, model: type) -> Select:
    """Order so the caller's own rows come before legacy NULL-org rows.

    Seed data gives every organization the *same* natural codes
    (``WH-001``, ``SKU-001``, ``TRUCK-1001``), so a lookup that
    ``scoped_to_organization(..., include_legacy_null=True)``-matches can see
    **two** matching rows: the caller's own and a legacy unattributed one. A
    bare ``scalar_one_or_none()`` then either raises
    ``MultipleResultsFound`` (HTTP 500) or silently returns whichever row the
    database happens to hand back — which for a write path means mutating
    another tenant's record.

    Callers must pair this with ``.first()`` (never ``scalar_one_or_none``).
    PostgreSQL places NULLs last for ``ASC``, and SQLite orders NULLs first, so
    an explicit ``IS NULL`` key is used to make the intent dialect-independent.
    """
    return query.order_by(model.organization_id.is_(None).asc())


def organization_scoped_get(
    db: Session,
    model: type,
    entity_id: str | UUID,
    organization_id: UUID | None,
    *,
    not_found_detail: str,
    include_legacy_null: bool = True,
) -> Any:
    """Load one row by id, returning 404 when it belongs to another tenant.

    Cross-tenant access answers **404, never 403**, so the existence of another
    organization's record is never leaked
    (``docs/behaviors/production-security-hardening.md`` §4).
    """
    row = db.get(model, entity_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    if organization_id is not None:
        row_org = row.organization_id
        if row_org is not None and row_org != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
        if row_org is None and not include_legacy_null:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    return row


def resolve_scoped_organization(actor: User | None, writable: Any) -> UUID | None:
    """Organization id for write paths: prefer the resolved writable workspace.

    ``require_writable_workspace`` already resolved (and lock-checked) the
    caller's membership, so reuse it rather than querying twice.
    """
    if writable is not None:
        return writable.organization_id
    return None
