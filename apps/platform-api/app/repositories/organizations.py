from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def __init__(self, db: Session):
        super().__init__(db)

    def slug_exists(self, slug: str) -> bool:
        return self.db.execute(
            select(Organization.id).where(Organization.slug == slug)
        ).first() is not None
