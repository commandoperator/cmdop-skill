"""Skill publish — collect files and upload to CMDOP marketplace."""

from __future__ import annotations

import base64
import fnmatch
import re
from pathlib import Path
from typing import Any, Literal

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

    skill_md = path / "skill.md"
    if not skill_md.exists():
        raise FileNotFoundError(
            f"skill.md not found in {path}. "
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


def parse_skill_manifest(path: Path) -> dict[str, str]:
    """Parse YAML frontmatter from skill.md.

    Extracts simple key: value pairs between --- delimiters.

    Returns:
        Dict with keys like name, version, description.
    """
    skill_md = path / "skill.md" if path.is_dir() else path
    if not skill_md.exists():
        raise FileNotFoundError(f"skill.md not found: {skill_md}")

    text = skill_md.read_text(encoding="utf-8")

    # Extract frontmatter block
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError("skill.md is missing YAML frontmatter (--- delimiters)")

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon = line.find(":")
        if colon == -1:
            continue
        key = line[:colon].strip()
        value = line[colon + 1 :].strip()
        frontmatter[key] = value

    if "name" not in frontmatter:
        raise ValueError("skill.md frontmatter must contain 'name'")
    if "version" not in frontmatter:
        raise ValueError("skill.md frontmatter must contain 'version'")

    return frontmatter


async def publish_skill(
    path: Path,
    api_key: str,
    base_url: str | None = None,
    mode: Literal["prod", "dev", "local"] = "prod",
) -> dict[str, Any]:
    """Publish a skill to the CMDOP marketplace.

    Collects files, parses manifest, creates or updates the skill,
    and uploads a new version.

    Args:
        path: Path to skill directory (must contain skill.md)
        api_key: CMDOP API key (cmdop_*)
        base_url: Custom API base URL (overrides mode)
        mode: Environment mode

    Returns:
        Result dict with ok, skill slug, version info
    """
    from cmdop_skill.api.client import CMDOPSkillsAPI

    path = Path(path).resolve()

    # 1. Parse manifest
    manifest = parse_skill_manifest(path)
    name = manifest["name"]
    version = manifest["version"]
    description = manifest.get("description", "")

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
            await api.skills.create(
                name=name,
                short_description=description[:200] if description else "",
                description=description,
            )

        # Create version with files
        ver = await api.skills.create_version(
            slug=slug,
            version=version,
            files=file_payloads,
        )

    return {
        "ok": True,
        "skill": slug,
        "version": version,
        "files_count": len(file_payloads),
        "created": not skill_exists,
        "version_id": str(getattr(ver, "id", "")),
    }
