from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/supply_chain'
    jwt_secret_key: str = 'change-me-in-production-minimum-32-bytes'
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 120
    password_salt: str = 'supply-chain-static-salt-change-me'
    provider_key_encryption_secret: str = 'change-me-provider-key-secret'
    cors_origins: list[str] = ['http://localhost:5173']
    allowed_hosts: list[str] = ['localhost', '127.0.0.1', 'testserver']
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
    app_env: str = 'development'
    log_level: str = 'INFO'

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
