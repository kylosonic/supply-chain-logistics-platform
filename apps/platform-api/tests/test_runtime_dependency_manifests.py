from __future__ import annotations

from pathlib import Path
import re
import tomllib


def _normalize_name(requirement: str) -> str:
    token = re.split(r'[<>=!~\[]', requirement.strip(), maxsplit=1)[0]
    return token.strip().lower()


def _pyproject_dependency_names(pyproject_path: Path) -> set[str]:
    data = tomllib.loads(pyproject_path.read_text(encoding='utf-8'))
    return {_normalize_name(dep) for dep in data['project']['dependencies']}


def _requirements_dependency_names(requirements_path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in requirements_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        names.add(_normalize_name(line))
    return names


def test_runtime_dependency_manifests_stay_aligned():
    root = Path(__file__).resolve().parent.parent
    pyproject_names = _pyproject_dependency_names(root / 'pyproject.toml')
    requirements_names = _requirements_dependency_names(root / 'requirements.txt')

    assert pyproject_names == requirements_names