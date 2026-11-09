from sqlalchemy import Column, String, Text
from app.db.base import Base
from app.models.common import UUIDTimestampMixin

class Feedback(UUIDTimestampMixin, Base):
    __tablename__ = 'feedback'
    
    category = Column(String, index=True, nullable=False)
    message = Column(Text, nullable=False)
    user_email = Column(String, nullable=True)
