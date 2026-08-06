from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from decimal import Decimal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_env: str = 'development'
    log_level: str = 'INFO'
    database_url: str = ''
    jwt_secret_key: str = ''
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 120
    provider_key_encryption_secret: str = ''
    cors_origins: list[str] = [
        'http://localhost',
        'http://localhost:5173',
        'http://localhost:3000',
        'http://localhost:8081',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8081',
    ]
    allowed_hosts: list[str] = ['localhost', '127.0.0.1', 'testserver']
    cbe_account_holder: str = ''
    cbe_account_number: str = ''
    dashen_account_holder: str = ''
    dashen_account_number: str = ''
    blocked_public_email_domains: list[str] = [
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
    receipt_max_size_bytes: int = 5 * 1024 * 1024
    wallet_auto_forward_tolerance_etb: Decimal = Decimal('1000.00')
    reversal_undo_window_hours: int = 24
    sms_brand_name: str = 'FreightPilot'
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
            return self.jwt_secret_key
        if self.app_env in ('development', 'test'):
            return 'dev-secret-do-not-use-in-production-minimum-32'
        raise ValueError('JWT_SECRET_KEY is required in non-dev environments')

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(',') if origin.strip()]
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
