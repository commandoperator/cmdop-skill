"""Skill publish — collect files and upload to CMDOP marketplace."""

from __future__ import annotations

import base64
import fnmatch
import importlib.util
from pathlib import Path
from typing import Any, Literal

DEFAULT_REPOSITORY_URL = "https://github.com/commandoperator/cmdop-skills-lab"

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
            content = item.read_text(encoding="utf-8")
            if not content:
                continue
            entry["content"] = content
        else:
            raw = item.read_bytes()
            if not raw:
                continue
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
        return config.model_dump(mode="json")
    if isinstance(config, dict):
        return config
    raise ValueError(
        f"skill/config.py `config` must be a SkillConfig instance or dict, "
        f"got {type(config).__name__}"
    )


def parse_skill_manifest(path: Path) -> dict[str, Any]:
    """Load skill manifest from ``skill/config.py``, enriched by ``pyproject.toml``.

    ``pyproject.toml`` fills in missing fields; ``skill/config.py`` always wins.

    Returns:
        Dict with at least ``name`` and ``version`` keys.
    """
    from cmdop_skill._resolve import read_pyproject_full

    base = path if path.is_dir() else path.parent

    config_py = base / "skill" / "config.py"
    if not config_py.is_file():
        raise FileNotFoundError(
            f"skill/config.py not found in {base}. "
            "Create a skill/config.py with a SkillConfig instance."
        )

    manifest = _load_skill_config(config_py)

    # Backfill empty fields from pyproject.toml
    pyproject = read_pyproject_full(base)
    for key, value in pyproject.items():
        if not manifest.get(key):
            manifest[key] = value

    if not manifest.get("version"):
        raise ValueError(
            "version is required. Set it in skill/config.py or pyproject.toml."
        )

    return manifest


def _read_file(path: Path) -> str:
    """Read file as text, return empty string if missing."""
    return path.read_text(encoding="utf-8") if path.is_file() else ""


async def publish_skill(
    path: Path,
    api_key: str,
    base_url: str | None = None,
    mode: Literal["prod", "dev", "local"] = "prod",
) -> dict[str, Any]:
    """Publish a skill to the CMDOP marketplace.

    Sends raw manifest + skill.md + README to Django.
    Server accepts the request (202) and processes asynchronously.

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

    # 1. Parse manifest (local — for name, version, metadata)
    m = parse_skill_manifest(path)
    name = m["name"]
    version = m["version"]

    # 2. Read raw files to send to Django
    raw_manifest = _read_file(path / "pyproject.toml")
    skill_md = _read_file(path / "skill" / "readme.md")
    readme = _read_file(path / "README.md") or _read_file(path / "readme.md")

    if not raw_manifest:
        raise FileNotFoundError(f"pyproject.toml not found in {path}")

    # 3. Publish via API
    api_kwargs: dict[str, Any] = {"api_key": api_key, "mode": mode}
    if base_url:
        api_kwargs["base_url"] = base_url

    async with CMDOPSkillsAPI(**api_kwargs) as api:
        slug = name
        skill_exists = False

        # Check if skill exists AND belongs to current user
        try:
            existing = await api.skills.get(slug)
            # get() returns skill — check ownership via my() list
            my_skills = await api.skills.my()
            my_slugs = {s.slug for s in (my_skills.results or [])}
            if slug in my_slugs:
                skill_exists = True
            else:
                raise ValueError(
                    f"Skill '{slug}' already exists and belongs to another user. "
                    "Choose a different name."
                )
        except ValueError:
            raise
        except Exception:
            skill_exists = False

        # Create skill if new
        if not skill_exists:
            try:
                await api.skills.create(name=name)
            except Exception:
                # Response parsing may fail, but skill may be created — verify.
                my_skills = await api.skills.my()
                my_slugs = {s.slug for s in (my_skills.results or [])}
                if slug not in my_slugs:
                    raise ValueError(f"Failed to create skill '{name}' on server")

        # Publish: raw_manifest → Django processes async (returns 202)
        try:
            await api.skills.publish(
                slug=slug,
                raw_manifest=raw_manifest,
                skill_md=skill_md or None,
                readme=readme or None,
                changelog=m.get("changelog"),
            )
        except Exception as exc:
            import httpx
            if isinstance(exc, httpx.HTTPStatusError):
                try:
                    body = exc.response.json()
                    msg = body.get('message') or body.get('detail') or str(body)
                except Exception:
                    msg = exc.response.text or str(exc)
                raise ValueError(f"Publish failed ({exc.response.status_code}): {msg}") from exc
            raise

    return {
        "ok": True,
        "skill": slug,
        "version": version,
        "created": not skill_exists,
    }
