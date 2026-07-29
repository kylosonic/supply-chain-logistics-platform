from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.user import User


def resolve_actor_organization_id(db: Session, user: User | None) -> str | None:
    if user is None:
        return None

    membership = db.execute(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.is_active.is_(True),
        )
        .order_by(OrganizationMembership.created_at.asc())
    ).scalar_one_or_none()
    return membership.organization_id if membership else None


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    description: str,
    actor: User | None = None,
    entity_id: str | None = None,
    organization_id: str | None = None,
    payload: dict[str, Any] | list[Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor.id if actor else None,
        organization_id=organization_id or resolve_actor_organization_id(db, actor),
        description=description,
        payload=payload,
    )
    db.add(event)
    return event