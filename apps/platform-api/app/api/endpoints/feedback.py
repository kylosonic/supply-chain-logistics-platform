from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackRead

router = APIRouter()

@router.post('', response_model=FeedbackRead)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db)
):
    feedback = Feedback(
        category=payload.category,
        message=payload.message,
        user_email=payload.user_email
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
