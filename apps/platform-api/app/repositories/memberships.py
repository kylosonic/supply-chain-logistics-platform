from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import OrganizationMembership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[OrganizationMembership]):
    model = OrganizationMembership

    def __init__(self, db: Session):
        super().__init__(db)

    def get_active_membership(self, user_id: str, org_id: str | None = None) -> OrganizationMembership | None:
        query = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active.is_(True),
        )
        if org_id:
            query = query.where(OrganizationMembership.organization_id == org_id)
        query = query.order_by(OrganizationMembership.created_at.desc())
        return self.db.execute(query).scalars().first()

    def get_organization_id_for_user(self, user_id: str) -> str | None:
        membership = self.db.execute(
            select(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_active.is_(True),
            )
            .order_by(OrganizationMembership.created_at.asc())
        ).scalar_one_or_none()
        return membership.organization_id if membership else None
