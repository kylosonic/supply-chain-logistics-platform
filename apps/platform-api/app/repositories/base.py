from __future__ import annotations

from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

T = TypeVar('T', bound=Base)


class BaseRepository[T]:
    model: type[T]

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: str | UUID) -> T | None:
        return self.db.get(self.model, id)

    def get_all(self, limit: int | None = None, offset: int = 0) -> list[T]:
        stmt = select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def add(self, instance: T) -> T:
        if not instance.id:
            instance.id = uuid4()
        self.db.add(instance)
        return instance

    def add_all(self, instances: list[T]) -> list[T]:
        for instance in instances:
            if not instance.id:
                instance.id = uuid4()
        self.db.add_all(instances)
        return instances

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: T) -> T:
        self.db.refresh(instance)
        return instance
