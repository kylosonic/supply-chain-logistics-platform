from __future__ import annotations

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models.route import RouteSchedule
from app.models.route_history import RouteOptimizationRun
from app.repositories.base import BaseRepository


class RouteScheduleRepository(BaseRepository[RouteSchedule]):
    model = RouteSchedule

    def __init__(self, db: Session):
        super().__init__(db)

    def list_all_sorted(self) -> list[RouteSchedule]:
        return list(
            self.db.execute(
                select(RouteSchedule).order_by(
                    asc(RouteSchedule.schedule_date), asc(RouteSchedule.route_name)
                )
            ).scalars().all()
        )


class RouteOptimizationRunRepository(BaseRepository[RouteOptimizationRun]):
    model = RouteOptimizationRun

    def __init__(self, db: Session):
        super().__init__(db)

    def list_all_desc(self) -> list[RouteOptimizationRun]:
        return list(
            self.db.execute(
                select(RouteOptimizationRun).order_by(desc(RouteOptimizationRun.created_at))
            ).scalars().all()
        )
