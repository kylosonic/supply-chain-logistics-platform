from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.usage_meter import OrganizationUsageCounter


def current_usage_window(reference_day: date) -> tuple[date, date]:
    period_start = reference_day.replace(day=1)
    next_month_start = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    period_end = next_month_start - timedelta(days=1)
    return period_start, period_end


def record_usage_for_user_membership(
    db: Session,
    *,
    organization_id: UUID,
    metric: str = 'delivery_tasks',
    units: int = 1,
    occurred_at: datetime | None = None,
) -> bool:
    if units <= 0:
        return False

    event_time = occurred_at or datetime.now(UTC)
    event_time = (
        event_time.replace(tzinfo=UTC)
        if event_time.tzinfo is None
        else event_time.astimezone(UTC)
    )

    period_start, period_end = current_usage_window(event_time.date())

    counter = db.execute(
        select(OrganizationUsageCounter).where(
            OrganizationUsageCounter.organization_id == organization_id,
            OrganizationUsageCounter.metric == metric,
            OrganizationUsageCounter.period_start == period_start,
        )
    ).scalar_one_or_none()

    if not counter:
        counter = OrganizationUsageCounter(
            organization_id=organization_id,
            metric=metric,
            period_start=period_start,
            period_end=period_end,
            used_units=0,
        )
        db.add(counter)
        db.flush()

    db.execute(
        update(OrganizationUsageCounter)
        .where(OrganizationUsageCounter.id == counter.id)
        .values(
            used_units=OrganizationUsageCounter.used_units + units,
            period_end=period_end,
            updated_at=datetime.now(UTC),
        )
    )
    return True
