import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.router import api_router
from app.core.config import settings
from app.core.observability import app_metrics
from app.db.session import engine

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger('app.http')

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200/minute'] if settings.app_env not in ('development', 'test') else [],
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # NB-63.1 (audit C-1): touch every effective_* property at boot so a
    # misconfigured non-dev environment aborts startup with an error naming
    # the offending variable, instead of failing lazily on first use.
    # Dev/test guards skip, so the pytest suite is unaffected.
    settings.effective_database_url
    settings.effective_jwt_secret_key
    settings.effective_provider_key_encryption_secret
    settings.effective_receipt_extraction_mode
    settings.effective_cbe_account_holder
    settings.effective_cbe_account_number
    settings.effective_dashen_account_holder
    settings.effective_dashen_account_number
    yield


app = FastAPI(title='Supply Chain Logistics API', version='1.0.0', lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda _request, _exc: JSONResponse(status_code=429, content={'detail': 'Too many requests'}))
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials='*' not in settings.cors_origins,
    allow_methods=['*'],
    allow_headers=['*'],
)

if settings.effective_allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.effective_allowed_hosts)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('x-request-id') or str(uuid4())
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        app_metrics.record_http(response.status_code)
        logger.info(
            'request_completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s',
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


app.add_middleware(RequestContextMiddleware)
app.include_router(api_router, prefix='/api/v1')


@app.get('/health')
def health() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        db_status = 'ok'
    except Exception:
        db_status = 'unavailable'
    # NB-71 (audit L-3): the environment name is deployment detail and is not
    # returned on a publicly reachable endpoint. Liveness/readiness consumers
    # only need the two status fields below.
    return {'status': 'ok' if db_status == 'ok' else 'degraded', 'db': db_status}
