from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_engine_kwargs = {
    'pool_pre_ping': True,
    'echo': settings.app_env == 'development',
}

if settings.effective_database_url.startswith('postgresql'):
    _engine_kwargs.update({
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
    })

engine = create_engine(settings.effective_database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
