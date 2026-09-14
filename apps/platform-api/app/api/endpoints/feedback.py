from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.security import get_current_user
from app.db.session import get_db
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackRead

router = APIRouter()

@router.post('', response_model=FeedbackRead)
def submit_feedback(
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback = Feedback(
        category=payload.category,
        message=payload.message,
        user_email=payload.user_email or user.email
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackRead(
        id=str(feedback.id),
        category=feedback.category,
        message=feedback.message,
        user_email=feedback.user_email,
        created_at=feedback.created_at,
        updated_at=None,
    )
