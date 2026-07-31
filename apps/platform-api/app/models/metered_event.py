from sqlalchemy import Column, String, Integer, ForeignKey
from app.db.base import Base
from app.models.common import UUIDTimestampMixin

class MeteredEvent(UUIDTimestampMixin, Base):
    __tablename__ = 'metered_events'
    
    organization_id = Column(String, ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    units = Column(Integer, default=1, nullable=False)
    description = Column(String, nullable=True)
