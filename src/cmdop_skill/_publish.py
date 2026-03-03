"""Skill publish — collect files and upload to CMDOP marketplace."""

from __future__ import annotations

import base64
import fnmatch
import importlib.util
from pathlib import Path
from typing import Any, Literal

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

IGNORE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    "node_modules",
    "data",
    ".venv",
    "venv",
    ".mypy_cache",
    ".ruff_cache",
}

IGNORE_FILE_PATTERNS = {
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.db",
    "*.log",
    "*.sqlite3",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".js",
    ".ts",
    ".css",
    ".html",
    ".cfg",
    ".ini",
    ".env.example",
}


def _is_ignored_file(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in IGNORE_FILE_PATTERNS)


def _has_skill_manifest(path: Path) -> bool:
    """Return True if *path* contains ``skill/config.py``."""
    return (path / "skill" / "config.py").is_file()


def collect_skill_files(path: Path) -> list[dict[str, Any]]:
    """Collect all publishable files from a skill directory.

    Walks the directory, skips ignored dirs/files, reads content.
    Text files are read as UTF-8; binary files are base64-encoded.

    Returns:
        List of dicts with keys: path, content, is_binary
    """
    path = path.resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Skill directory not found: {path}")

    if not _has_skill_manifest(path):
        raise FileNotFoundError(
            f"skill/config.py not found in {path}. "
            "This file is required — it's the skill manifest."
        )

    files: list[dict[str, Any]] = []

    for item in sorted(path.rglob("*")):
        if not item.is_file():
            continue

        # Check if any parent directory is ignored
        rel = item.relative_to(path)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue

        if _is_ignored_file(item.name):
            continue

        is_text = item.suffix.lower() in TEXT_EXTENSIONS
        entry: dict[str, Any] = {"path": str(rel), "size": item.stat().st_size}

        if is_text:
            entry["content"] = item.read_text(encoding="utf-8")
        else:
            raw = item.read_bytes()
            entry["content"] = base64.b64encode(raw).decode("ascii")
            entry["is_binary"] = True

        files.append(entry)

    return files


def _load_skill_config(config_path: Path) -> dict[str, Any]:
    """Load ``skill/config.py`` and return the ``config`` object as dict.

    Uses ``importlib.util`` so we never import the skill's own dependencies.
    """
    spec = importlib.util.spec_from_file_location("_skill_config", config_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load module spec from {config_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    config = getattr(mod, "config", None)
    if config is None:
        raise ValueError(
            f"skill/config.py must define a module-level `config` variable "
            f"(SkillConfig instance): {config_path}"
        )

    # Accept both SkillConfig (pydantic) and plain dict
    if hasattr(config, "model_dump"):
        return config.model_dump()
    if isinstance(config, dict):
        return config
    raise ValueError(
        f"skill/config.py `config` must be a SkillConfig instance or dict, "
        f"got {type(config).__name__}"
    )


def _read_pyproject(base: Path) -> dict[str, Any]:
    """Extract SkillConfig-compatible fields from ``pyproject.toml``."""
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
    if urls.get("Repository"):
        result["repository_url"] = urls["Repository"]
    return result


def parse_skill_manifest(path: Path) -> dict[str, Any]:
    """Load skill manifest from ``skill/config.py``, enriched by ``pyproject.toml``.

    ``pyproject.toml`` fills in missing fields; ``skill/config.py`` always wins.

    Returns:
        Dict with at least ``name`` and ``version`` keys.
    """
    base = path if path.is_dir() else path.parent

    config_py = base / "skill" / "config.py"
    if not config_py.is_file():
        raise FileNotFoundError(
            f"skill/config.py not found in {base}. "
            "Create a skill/config.py with a SkillConfig instance."
        )

    manifest = _load_skill_config(config_py)

    # Backfill empty fields from pyproject.toml
    pyproject = _read_pyproject(base)
    for key, value in pyproject.items():
        if not manifest.get(key):
            manifest[key] = value

    if not manifest.get("version"):
        raise ValueError(
            "version is required. Set it in skill/config.py or pyproject.toml."
        )

    return manifest


async def publish_skill(
    path: Path,
    api_key: str,
    base_url: str | None = None,
    mode: Literal["prod", "dev", "local"] = "prod",
) -> dict[str, Any]:
    """Publish a skill to the CMDOP marketplace.

    Args:
        path: Path to skill directory (must contain skill/config.py)
        api_key: CMDOP API key (cmdop_*)
        base_url: Custom API base URL (overrides mode)
        mode: Environment mode

    Returns:
        Result dict with ok, skill slug, version info
    """
    from cmdop_skill.api.client import CMDOPSkillsAPI

    path = Path(path).resolve()

    # 1. Parse manifest
    m = parse_skill_manifest(path)
    name = m["name"]
    version = m["version"]

    # 2. Collect files
    files = collect_skill_files(path)
    file_payloads = [{"path": f["path"], "content": f["content"]} for f in files]

    # 3. Publish via API
    api_kwargs: dict[str, Any] = {"api_key": api_key, "mode": mode}
    if base_url:
        api_kwargs["base_url"] = base_url

    async with CMDOPSkillsAPI(**api_kwargs) as api:
        # Check if skill exists
        slug = name
        skill_exists = True
        try:
            await api.skills.get(slug)
        except Exception:
            skill_exists = False

        # Create skill if new
        if not skill_exists:
            create_kwargs: dict[str, Any] = {
                "name": name,
                "short_description": m.get("short_description", "")
                or (m.get("description", "")[:300]),
                "description": m.get("description", ""),
            }
            if m.get("category"):
                create_kwargs["category"] = m["category"]
            if m.get("tags"):
                create_kwargs["tags"] = m["tags"]
            if m.get("visibility"):
                create_kwargs["visibility"] = m["visibility"]
            if m.get("repository_url"):
                create_kwargs["repository_url"] = m["repository_url"]

            await api.skills.create(**create_kwargs)

        # Create version with files
        ver_kwargs: dict[str, Any] = {
            "slug": slug,
            "version": version,
            "files": file_payloads,
        }
        if m.get("changelog"):
            ver_kwargs["changelog"] = m["changelog"]

        ver = await api.skills.create_version(**ver_kwargs)

    return {
        "ok": True,
        "skill": slug,
        "version": version,
        "files_count": len(file_payloads),
        "created": not skill_exists,
        "version_id": str(getattr(ver, "id", "")),
    }
