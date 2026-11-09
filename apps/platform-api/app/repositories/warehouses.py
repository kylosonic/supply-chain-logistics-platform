from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.repositories.base import BaseRepository


class WarehouseRepository(BaseRepository[Warehouse]):
    model = Warehouse

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_code(self, code: str, organization_id: str | None = None) -> Warehouse | None:
        query = select(Warehouse).where(Warehouse.code == code)
        if organization_id:
            query = query.where(Warehouse.organization_id == organization_id)
        return self.db.execute(query).scalar_one_or_none()

