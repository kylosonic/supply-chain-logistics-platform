"""Chain-integrity regression test for the alembic revision chain.

Regex-parses ``revision`` / ``down_revision`` from every migration module
without importing them (blueprint §2b). Hard-gates: linear chain, no
duplicates, exactly one head, head is 0017.
"""
from __future__ import annotations

import re
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'alembic' / 'versions'

_REVISION_RE = re.compile(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_DOWN_REVISION_RE = re.compile(r"^down_revision\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)


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


def test_migration_chain_is_linear_and_head_is_0018():
    migrations = _parse_migrations()
    assert len(migrations) >= 16, 'expected the full 0001..0018 chain'

    # No duplicate revision ids.
    assert len({revision for revision in migrations}) == len(migrations)

    # Every down_revision resolves to a known revision (root may be None).
    known = set(migrations)
    for revision, (down, filename) in migrations.items():
        if down is not None:
            assert down in known, f'{filename}: down_revision {down!r} does not exist'

    # Exactly one head, and it must be 0018 (drift repair).
    referenced = {down for down, _filename in migrations.values() if down is not None}
    heads = [revision for revision in known if revision not in referenced]
    assert heads == ['20260808_0018'], f'unexpected head(s): {heads}'

    # 0018 sits directly on 0017.
    assert migrations['20260808_0018'][0] == '20260806_0017'
