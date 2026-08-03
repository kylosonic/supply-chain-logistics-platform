from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    model = Item

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_sku(self, sku: str, organization_id: str | None = None) -> Item | None:
        query = select(Item).where(Item.sku == sku)
        if organization_id:
            query = query.where(Item.organization_id == organization_id)
        return self.db.execute(query).scalar_one_or_none()
