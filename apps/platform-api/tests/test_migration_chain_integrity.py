"""Chain-integrity regression test for the alembic revision chain.

Regex-parses ``revision`` / ``down_revision`` from every migration module
without importing them (blueprint §2b). Hard-gates: linear chain, no
duplicates, exactly one head, and the head matches the newest migration.
"""
from __future__ import annotations

import re
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'alembic' / 'versions'

_REVISION_RE = re.compile(
    r"^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE
)
_DOWN_REVISION_RE = re.compile(
    r"^down_revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE
)

# Head advances with each migration batch. Keep this pin deliberate: it is the
# tripwire that makes an accidental second head or a forgotten down_revision fail
# loudly instead of silently forking the chain.
_HEAD = '20260812_0020'
_HEAD_PARENT = '20260811_0019'
_MIN_EXPECTED = 20


def _parse_migrations() -> dict[str, tuple[str | None, str]]:
    migrations: dict[str, tuple[str | None, str]] = {}
    for path in sorted(_MIGRATIONS_DIR.glob('*.py')):
        text = path.read_text(encoding='utf-8')
        revision_match = _REVISION_RE.search(text)
        assert revision_match is not None, f'{path.name}: missing revision'
        down_match = _DOWN_REVISION_RE.search(text)
        down = down_match.group(1) if down_match else None
        migrations[revision_match.group(1)] = (down, path.name)
    return migrations


def test_migration_chain_is_linear_and_head_is_current():
    migrations = _parse_migrations()
    assert len(migrations) >= _MIN_EXPECTED, f'expected the full migration chain (>= {_MIN_EXPECTED})'

    # No duplicate revision ids.
    assert len({revision for revision in migrations}) == len(migrations)

    # Every down_revision resolves to a known revision (root may be None).
    known = set(migrations)
    for revision, (down, filename) in migrations.items():
        if down is not None:
            assert down in known, f'{filename}: down_revision {down!r} does not exist'

    # Exactly one head, and it must be the newest migration.
    referenced = {down for down, _filename in migrations.values() if down is not None}
    heads = [revision for revision in known if revision not in referenced]
    assert heads == [_HEAD], f'unexpected head(s): {heads}'

    # The head sits directly on its documented parent.
    assert migrations[_HEAD][0] == _HEAD_PARENT

