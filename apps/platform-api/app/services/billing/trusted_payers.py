"""Per-org trusted-payer list (TECH-11 / NB-11). Admin-only surface.

Imports models + audit only.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.trusted_payer import TrustedPayer
from app.models.user import User
from app.services.audit import record_audit_event


def normalize_sender(name: str) -> str:
    """casefold + strip + collapse whitespace (blueprint §2.1)."""
    return re.sub(r'\s+', ' ', name.casefold().strip())


def is_trusted(db: Session, org_id, sender_name: str | None) -> bool:
    if not sender_name:
        return False
    row = db.execute(
        select(TrustedPayer.id).where(
            TrustedPayer.organization_id == org_id,
            TrustedPayer.sender_name == normalize_sender(sender_name),
        ).limit(1)
    ).first()
    return row is not None


def add_trusted_payer(db: Session, org: Organization, sender_name: str, admin_user: User | None) -> TrustedPayer | None:
    """Idempotent add (blueprint §5); audits ``receipts.trusted_payer_added``."""
    normalized = normalize_sender(sender_name)
    existing = db.execute(
        select(TrustedPayer).where(
            TrustedPayer.organization_id == org.id,
            TrustedPayer.sender_name == normalized,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return None
    row = TrustedPayer(
        organization_id=org.id,
        sender_name=normalized,
        added_by_user_id=admin_user.id if admin_user else None,
    )
    db.add(row)
    record_audit_event(
        db,
        event_type='receipts.trusted_payer_added',
        entity_type='organization',
        entity_id=org.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Added trusted payer {normalized}',
        payload={'sender_name': normalized},
    )
    return row


def remove_trusted_payer(
    db: Session, org: Organization, sender_name: str, admin_user: User | None
) -> bool | None:
    """Remove a trusted payer (NB-21.5); returns True on removal, None when
    the row is missing (the endpoint maps None -> 404 — this module keeps
    its error surface unchanged).

    The fraud flag is deliberately NOT cleared (decision #6): the badge
    survives list removal. Audits ``receipts.trusted_payer_removed``.
    """
    normalized = normalize_sender(sender_name)
    row = db.execute(
        select(TrustedPayer).where(
            TrustedPayer.organization_id == org.id,
            TrustedPayer.sender_name == normalized,
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    db.delete(row)
    record_audit_event(
        db,
        event_type='receipts.trusted_payer_removed',
        entity_type='organization',
        entity_id=org.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Removed trusted payer {normalized}',
        payload={'sender_name': normalized},
    )
    return True
