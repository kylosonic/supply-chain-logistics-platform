from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import get_current_membership
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.notification import Notification
from app.schemas.billing import NotificationRead

router = APIRouter()


@router.get('', response_model=list[NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    rows = db.execute(
        select(Notification)
        .where(Notification.organization_id == membership.organization_id)
        .order_by(Notification.created_at.desc())
    ).scalars().all()
    return rows


@router.post('/{notification_id}/dismiss', response_model=NotificationRead)
def dismiss_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    notification = db.get(Notification, notification_id)
    if not notification or notification.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Notification not found')

    expires_at = notification.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if datetime.now(UTC) < expires_at:
        raise HTTPException(
            status_code=409,
            detail='Notification persists for its full warning window',
        )

    notification.dismissed_at = datetime.now(UTC)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
