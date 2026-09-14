"""NB-63.3/NB-63.4 static hygiene scans (audit C-1).

Pins that no committed environment example ships a placeholder secret value
long enough to pass the production guards, and that docker-compose carries
no secret defaults, binds the postgres port to host loopback only, and uses
required ``:?`` interpolation for the three secrets.

Precedent: ``test_prod_sample_data_packaging.py`` reads repo files statically.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import KNOWN_PLACEHOLDER_SECRETS

PLATFORM_API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

PLATFORM_API_ENV_EXAMPLE = PLATFORM_API_DIR / '.env.example'
ROOT_ENV_EXAMPLE = REPO_ROOT / '.env.example'
DOCKER_COMPOSE = REPO_ROOT / 'docker-compose.yml'


def _parse_env_example(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        values[key.strip()] = value.strip()
    return values


def test_platform_api_env_example_ships_empty_secrets():
    values = _parse_env_example(PLATFORM_API_ENV_EXAMPLE)
    assert values['JWT_SECRET_KEY'] == ''
    assert values['PROVIDER_KEY_ENCRYPTION_SECRET'] == ''
    for value in values.values():
        assert value not in KNOWN_PLACEHOLDER_SECRETS


def test_root_env_example_ships_empty_secrets():
    values = _parse_env_example(ROOT_ENV_EXAMPLE)
    assert values['JWT_SECRET_KEY'] == ''
    assert values['PROVIDER_KEY_ENCRYPTION_SECRET'] == ''
    assert values['POSTGRES_PASSWORD'] == ''
    for value in values.values():
        assert value not in KNOWN_PLACEHOLDER_SECRETS


def test_compose_has_no_secret_defaults_and_binds_loopback():
    text = DOCKER_COMPOSE.read_text(encoding='utf-8')
    # Required interpolation for the three secrets (fail-fast, no defaults).
    assert 'POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}' in text
    assert 'JWT_SECRET_KEY: ${JWT_SECRET_KEY:?JWT_SECRET_KEY must be set}' in text
    assert (
        'PROVIDER_KEY_ENCRYPTION_SECRET: '
        '${PROVIDER_KEY_ENCRYPTION_SECRET:?PROVIDER_KEY_ENCRYPTION_SECRET must be set}'
    ) in text
    # Postgres published to host loopback only.
    assert '127.0.0.1:${POSTGRES_PORT:-5432}:5432' in text
    # No secret defaults remain anywhere (password fallback removed).
    assert '${POSTGRES_PASSWORD:-postgres}' not in text
    assert '${JWT_SECRET_KEY:-change-me-in-production}' not in text
    assert '${PROVIDER_KEY_ENCRYPTION_SECRET:-change-me-provider-key-secret-min-32-chars!}' not in text
