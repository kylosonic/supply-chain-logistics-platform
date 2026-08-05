"""Per-org sender fraud-risk ledger (TECH-21 / NB-21, decision #6).

``sender_fraud_flags`` is the persistent badge store: keyed
``(organization_id, normalized sender_name)`` UNIQUE, rows never
auto-deleted -> the badge survives trusted-payer list removal and persists
indefinitely (NB-21.3). Display-only: nothing here ever gates verification
(NB-21.4 / NB-21.6).

Imports: models + audit + ``trusted_payers.normalize_sender`` (leaf —
never imports anything from ``receipts``, keeping the graph acyclic).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.sender_fraud_flag import SenderFraudFlag
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.billing.trusted_payers import normalize_sender


def is_fraud_flagged(db: Session, org_id, sender_name: str | None) -> bool:
    """True when the org has a persistent fraud flag for this sender."""
    if not sender_name:
        return False
    row = db.execute(
        select(SenderFraudFlag.id).where(
            SenderFraudFlag.organization_id == org_id,
            SenderFraudFlag.sender_name == normalize_sender(sender_name),
        ).limit(1)
    ).first()
    return row is not None


def fraud_flag_read(db: Session, org_id, sender_name: str | None) -> SenderFraudFlag | None:
    """Full flag row (for queue payloads: ``fraud_risk_since``)."""
    if not sender_name:
        return None
    return db.execute(
        select(SenderFraudFlag).where(
            SenderFraudFlag.organization_id == org_id,
            SenderFraudFlag.sender_name == normalize_sender(sender_name),
        )
    ).scalar_one_or_none()


def flag_sender_fraud(
    db: Session,
    org: Organization,
    sender_name: str,
    admin_user: User | None,
    *,
    original_verified_event_id: str | None = None,
) -> SenderFraudFlag:
    """Upsert the flag: exists -> ``reversal_count += 1``; else insert with
    ``fraud_risk_since = now``. Audits ``receipts.fraud_flagged`` (NB-21.2)."""
    normalized = normalize_sender(sender_name)
    existing = db.execute(
        select(SenderFraudFlag).where(
            SenderFraudFlag.organization_id == org.id,
            SenderFraudFlag.sender_name == normalized,
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.reversal_count += 1
        row = existing
    else:
        row = SenderFraudFlag(
            organization_id=org.id,
            sender_name=normalized,
            fraud_risk_since=datetime.now(UTC),
            reversal_count=1,
        )
        db.add(row)
    record_audit_event(
        db,
        event_type='receipts.fraud_flagged',
        entity_type='organization',
        entity_id=org.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Fraud-risk flag set for sender {normalized}',
        payload={
            'sender_name': normalized,
            'reversal_count': row.reversal_count,
            'original_verified_event_id': original_verified_event_id,
        },
    )
    return row
