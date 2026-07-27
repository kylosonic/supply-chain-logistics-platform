import logging
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.observability import app_metrics

app = FastAPI(title="Supply Chain Logistics API", version="1.0.0")
logger = logging.getLogger('app.http')
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials='*' not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {'status': 'ok', 'env': settings.app_env}
