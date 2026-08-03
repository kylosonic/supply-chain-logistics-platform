from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_username(self, username: str) -> User | None:
        return self.db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def find_by_identifier(self, identifier: str) -> User | None:
        from sqlalchemy import or_

        return self.db.execute(
            select(User).where(
                or_(User.username == identifier, User.email == identifier)
            )
        ).scalar_one_or_none()

    def any_user_exists(self) -> bool:
        return self.db.execute(select(User.id).limit(1)).first() is not None

    def list_all(self) -> list[User]:
        return list(
            self.db.execute(select(User).order_by(User.username)).scalars().all()
        )
