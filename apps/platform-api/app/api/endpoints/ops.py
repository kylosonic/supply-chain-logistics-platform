from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.core.config import settings
from app.core.observability import app_metrics
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserRole

router = APIRouter()


@router.get('/ready')
def readiness(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text('SELECT 1'))
    except Exception as exc:
        raise HTTPException(status_code=503, detail='Database unavailable') from exc
    return {'status': 'ok', 'env': settings.app_env}


@router.get('/metrics')
def metrics(_: User = Depends(require_roles(UserRole.ADMIN))) -> dict:
    return app_metrics.snapshot()
