from decimal import Decimal
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


DEFAULT_CORS_ORIGINS = [
    'http://localhost',
    'http://localhost:5173',
    'http://localhost:3000',
    'http://localhost:5174',
    'http://localhost:8081',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5174',
    'http://127.0.0.1:8081',
    'https://product-web-chi.vercel.app',
    'https://ops-console-azure.vercel.app',
]

# NB-63 (audit C-1): every committed placeholder value that is long enough
# to pass the length-only guards. Exact-match rejection only — a secret that
# differs by a single character is a real secret decision
# (production-security-hardening.md:30). Dev/test environments stay permissive.
KNOWN_PLACEHOLDER_SECRETS = frozenset({
    'change-me-in-production',                                # 23 — docker-compose legacy JWT fallback
    'change-me-in-production-minimum-32-bytes',               # 40 — committed platform-api/.env.example value
    'change-me-provider-key-secret-min-32-chars!',            # 43 — committed provider encryption placeholder
    'dev-secret-do-not-use-in-production-minimum-32',         # 46 — dev fallback copy-pasted into prod
})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_env: str = 'development'
    log_level: str = 'INFO'
    database_url: str = ''
    jwt_secret_key: str = ''
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 120
    provider_key_encryption_secret: str = ''
    cors_origins: Annotated[list[str], NoDecode] = DEFAULT_CORS_ORIGINS.copy()
    allowed_hosts: Annotated[list[str], NoDecode] = [
        'localhost',
        '127.0.0.1',
        # 'testserver' is required by Starlette's TestClient Host header and is
        # never reachable in production — see the non-dev guard in
        # ``effective_allowed_hosts`` (NB-71 / audit L-2).
        'testserver',
        'platform-api-smoky.vercel.app',
    ]
    cbe_account_holder: str = ''
    cbe_account_number: str = ''
    dashen_account_holder: str = ''
    dashen_account_number: str = ''
    blocked_public_email_domains: Annotated[list[str], NoDecode] = [
        'gmail.com',
        'yahoo.com',
        'hotmail.com',
        'outlook.com',
        'live.com',
        'icloud.com',
        'aol.com',
        'proton.me',
        'protonmail.com',
    ]
    receipt_extraction_mode: str = 'mock'
    receipt_extraction_base_url: str = 'https://api.openai.com/v1'
    receipt_extraction_model: str = 'gpt-4o-mini'
    receipt_max_size_bytes: int = 5 * 1024 * 1024
    # NB-70 (audit M-4): CSV ingestion was unbounded — an authenticated
    # operator could stream an arbitrarily large body into memory.
    csv_max_size_bytes: int = 10 * 1024 * 1024
    wallet_auto_forward_tolerance_etb: Decimal = Decimal('1000.00')
    reversal_undo_window_hours: int = 24
    sms_brand_name: str = 'FreightPilot'
    sms_gateway_url: str = ''
    sms_gateway_api_key: str = ''
    sms_sender_name: str = 'FreightPilot'
    sample_data_dir: str = 'sample-data'

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.app_env in ('development', 'test'):
            return 'sqlite+pysqlite:///:memory:'
        raise ValueError('DATABASE_URL is required in non-dev environments')

    @property
    def effective_jwt_secret_key(self) -> str:
        if self.jwt_secret_key:
            if len(self.jwt_secret_key) < 32 and self.app_env not in ('development', 'test'):
                raise ValueError('JWT_SECRET_KEY must be at least 32 characters in non-dev environments')
            if (
                self.app_env not in ('development', 'test')
                and self.jwt_secret_key in KNOWN_PLACEHOLDER_SECRETS
            ):
                raise ValueError('JWT_SECRET_KEY must not be a known placeholder value')
            return self.jwt_secret_key
        if self.app_env in ('development', 'test'):
            return 'dev-secret-do-not-use-in-production-minimum-32'
        raise ValueError('JWT_SECRET_KEY is required in non-dev environments')

    @property
    def effective_receipt_extraction_mode(self) -> str:
        """Production mode guard: only ``real`` or ``zero_confidence`` are
        legal outside dev/test — ``mock`` can never leak into production."""
        if self.app_env in ('development', 'test'):
            return self.receipt_extraction_mode
        if self.receipt_extraction_mode not in ('real', 'zero_confidence'):
            raise ValueError(
                'RECEIPT_EXTRACTION_MODE must be "real" or "zero_confidence" '
                'in non-dev environments'
            )
        if self.receipt_extraction_mode == 'real' and not (
            self.receipt_extraction_base_url.startswith('http://')
            or self.receipt_extraction_base_url.startswith('https://')
        ):
            raise ValueError(
                'RECEIPT_EXTRACTION_BASE_URL must start with http:// or https:// in real mode'
            )
        return self.receipt_extraction_mode

    @property
    def effective_cbe_account_holder(self) -> str:
        if self.app_env in ('development', 'test'):
            return self.cbe_account_holder
        if not self.cbe_account_holder:
            raise ValueError('CBE_ACCOUNT_HOLDER is required in non-dev environments')
        return self.cbe_account_holder

    @property
    def effective_cbe_account_number(self) -> str:
        if self.app_env in ('development', 'test'):
            return self.cbe_account_number
        if not self.cbe_account_number:
            raise ValueError('CBE_ACCOUNT_NUMBER is required in non-dev environments')
        return self.cbe_account_number

    @property
    def effective_dashen_account_holder(self) -> str:
        if self.app_env in ('development', 'test'):
            return self.dashen_account_holder
        if not self.dashen_account_holder:
            raise ValueError('DASHEN_ACCOUNT_HOLDER is required in non-dev environments')
        return self.dashen_account_holder

    @property
    def effective_dashen_account_number(self) -> str:
        if self.app_env in ('development', 'test'):
            return self.dashen_account_number
        if not self.dashen_account_number:
            raise ValueError('DASHEN_ACCOUNT_NUMBER is required in non-dev environments')
        return self.dashen_account_number

    @property
    def effective_provider_key_encryption_secret(self) -> str:
        """Production secrets guard (PROD-05): non-empty and >= 32 chars in
        non-dev environments; dev/test return the raw value (empty allowed —
        legacy Fernet fallback to the JWT secret)."""
        if self.app_env in ('development', 'test'):
            return self.provider_key_encryption_secret
        if not self.provider_key_encryption_secret:
            raise ValueError('PROVIDER_KEY_ENCRYPTION_SECRET is required in non-dev environments')
        if len(self.provider_key_encryption_secret) < 32:
            raise ValueError(
                'PROVIDER_KEY_ENCRYPTION_SECRET must be at least 32 characters '
                'in non-dev environments'
            )
        if self.provider_key_encryption_secret in KNOWN_PLACEHOLDER_SECRETS:
            raise ValueError('PROVIDER_KEY_ENCRYPTION_SECRET must not be a known placeholder value')
        return self.provider_key_encryption_secret

    @property
    def effective_allowed_hosts(self) -> list[str]:
        """Allowed hosts actually enforced by ``TrustedHostMiddleware``.

        NB-71 (audit L-2): ``testserver`` is a Starlette TestClient artefact. It
        is needed for the test suite but must never be an accepted ``Host`` on a
        deployed environment, so it is dropped outside dev/test even if it
        appears in ``ALLOWED_HOSTS``.
        """
        if self.app_env in ('development', 'test'):
            return list(self.allowed_hosts)
        return [host for host in self.allowed_hosts if host != 'testserver']

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            parsed = [origin.strip() for origin in value.split(',') if origin.strip()]
            return parsed or DEFAULT_CORS_ORIGINS.copy()
        return value

    @field_validator('allowed_hosts', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [host.strip() for host in value.split(',') if host.strip()]
        return value

    @field_validator('blocked_public_email_domains', mode='before')
    @classmethod
    def parse_blocked_domains(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [domain.strip().lower() for domain in value.split(',') if domain.strip()]
        return [domain.lower() for domain in value]


settings = Settings()
