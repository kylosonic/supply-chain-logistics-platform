from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    category: str = Field(..., max_length=100)
    message: str = Field(..., max_length=2000)
    user_email: str | None = None


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    message: str
    user_email: str | None
    created_at: datetime
    updated_at: datetime | None
