"""Resolve project metadata from pyproject.toml — single source of truth."""

from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

_cache: dict[str, dict[str, str]] = {}


def _find_pyproject(start: Path) -> Path | None:
    """Walk up from *start* looking for ``pyproject.toml``."""
    current = start if start.is_dir() else start.parent
    for _ in range(20):  # safety limit
        candidate = current / "pyproject.toml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _caller_file() -> str | None:
    """Return the file path of the first caller outside this package."""
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    for frame_info in inspect.stack():
        fpath = frame_info.filename
        if fpath == "<string>":
            continue
        abs_fpath = os.path.abspath(fpath)
        if abs_fpath.startswith(pkg_dir):
            continue
        return abs_fpath
    return None


def resolve_project_meta(caller_file: str | None = None) -> dict[str, str]:
    """Resolve ``name``, ``version``, ``description`` from the nearest ``pyproject.toml``.

    Args:
        caller_file: Explicit file path to start searching from.
            If *None*, auto-detected via ``inspect.stack()``.

    Returns:
        Dict with ``name``, ``version``, ``description`` keys (empty string if missing).
    """
    if caller_file is None:
        caller_file = _caller_file()

    if caller_file is None:
        return {"name": "", "version": "", "description": ""}

    # Cache by resolved pyproject.toml path
    start = Path(caller_file)
    toml_path = _find_pyproject(start)
    if toml_path is None:
        return {"name": "", "version": "", "description": ""}

    cache_key = str(toml_path)
    if cache_key in _cache:
        return _cache[cache_key]

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    proj = data.get("project", {})
    result = {
        "name": proj.get("name", ""),
        "version": proj.get("version", ""),
        "description": proj.get("description", ""),
    }

    _cache[cache_key] = result
    return result


def read_pyproject_full(base: Path) -> dict[str, Any]:
    """Read all SkillConfig-compatible fields from ``pyproject.toml``.

    Used by ``_publish.py`` for the full set of publish metadata
    (tags, requires, repository_url, etc.).
    """
    from cmdop_skill._publish import DEFAULT_REPOSITORY_URL

    toml_path = base / "pyproject.toml"
    if not toml_path.is_file():
        return {}

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    proj = data.get("project", {})
    urls = proj.get("urls", {})

    result: dict[str, Any] = {}
    if proj.get("name"):
        result["name"] = proj["name"]
    if proj.get("version"):
        result["version"] = proj["version"]
    if proj.get("description"):
        result["short_description"] = proj["description"]
        result["description"] = proj["description"]
    if proj.get("dependencies"):
        result["requires"] = proj["dependencies"]
    if proj.get("keywords"):
        result["tags"] = proj["keywords"]
    result["repository_url"] = urls.get("Repository", DEFAULT_REPOSITORY_URL)
    return result
