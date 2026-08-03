from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.order import HistoricalOrder
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[HistoricalOrder]):
    model = HistoricalOrder

    def __init__(self, db: Session):
        super().__init__(db)

    def list_by_org(
        self, organization_id: str, skip: int = 0, limit: int = 200
    ) -> list[HistoricalOrder]:
        return list(
            self.db.execute(
                select(HistoricalOrder)
                .where(HistoricalOrder.organization_id == organization_id)
                .order_by(desc(HistoricalOrder.order_date))
                .offset(skip)
                .limit(limit)
            ).scalars().all()
        )
