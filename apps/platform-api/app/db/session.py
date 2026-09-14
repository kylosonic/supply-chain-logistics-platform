import sqlite3
from uuid import UUID

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

sqlite3.register_adapter(UUID, lambda u: str(u))

_engine_kwargs = {
    'pool_pre_ping': True,
    'echo': settings.app_env == 'development',
}

if settings.effective_database_url.startswith('postgresql'):
    _engine_kwargs.update({
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
        # NB-72/health: without a connect timeout a missing or firewalled
        # database makes every connect attempt hang for the OS TCP timeout
        # (~2 min), so ``GET /health`` never answers and the readiness probe
        # looks *up* while the database is actually down. Bound the connect
        # (and any transient statement) so the health surface fails fast and
        # reports ``degraded`` instead of hanging.
        'connect_args': {'connect_timeout': 5},
    })

engine = create_engine(settings.effective_database_url, **_engine_kwargs)


@event.listens_for(engine, 'connect')
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.execute('PRAGMA foreign_keys=ON')


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
