import logging
import time
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

app = FastAPI(title='Supply Chain Logistics API', version='1.0.0')
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

if settings.allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)


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
    return {'status': 'ok' if db_status == 'ok' else 'degraded', 'db': db_status, 'env': settings.app_env}
