from pydantic import BaseModel, Field
from datetime import datetime

class FeedbackCreate(BaseModel):
    category: str = Field(..., max_length=100)
    message: str = Field(..., max_length=2000)
    user_email: str | None = None

class FeedbackRead(BaseModel):
    id: str
    category: str
    message: str
    user_email: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
