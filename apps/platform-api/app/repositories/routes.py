from __future__ import annotations

from uuid import UUID

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.core.tenant_scope import scoped_to_organization
from app.models.route import RouteSchedule
from app.models.route_history import RouteOptimizationRun
from app.repositories.base import BaseRepository


class RouteScheduleRepository(BaseRepository[RouteSchedule]):
    model = RouteSchedule

    def __init__(self, db: Session):
        super().__init__(db)

    def list_all_sorted(self, organization_id: UUID | None = None) -> list[RouteSchedule]:
        # NB-64: optional tenant filter; None preserves the org-less listing.
        stmt = scoped_to_organization(select(RouteSchedule), RouteSchedule, organization_id)
        return list(
            self.db.execute(
                stmt.order_by(
                    asc(RouteSchedule.schedule_date), asc(RouteSchedule.route_name)
                )
            ).scalars().all()
        )


class RouteOptimizationRunRepository(BaseRepository[RouteOptimizationRun]):
    model = RouteOptimizationRun

    def __init__(self, db: Session):
        super().__init__(db)

    def list_all_desc(self, organization_id: UUID | None = None) -> list[RouteOptimizationRun]:
        # NB-64: optional tenant filter; None preserves the org-less listing.
        stmt = scoped_to_organization(
            select(RouteOptimizationRun), RouteOptimizationRun, organization_id
        )
        return list(
            self.db.execute(
                stmt.order_by(desc(RouteOptimizationRun.created_at))
            ).scalars().all()
        )
