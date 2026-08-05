"""Organization activation state (blueprint decision #1).

1:1 table with ``organizations``. Milestones 1-5 are DERIVED from real-row
presence at read time; only milestone 6 (first route optimization run) is
stored here alongside the toast flag and the seed timestamp.

Import map: db.base, db.custom_types, models.common, sqlalchemy only.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class OrganizationActivationState(UUIDTimestampMixin, Base):
    __tablename__ = 'organization_activation_state'

    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True,
    )
    m6_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    toast_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
