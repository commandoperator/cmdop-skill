"""Typed disk cache for CMDOP skills.

Stores JSON-serializable data under the platform-specific cmdop directory:
  - macOS:   ~/Library/Application Support/cmdop/cache/<skill>/<key>.json
  - Linux:   $XDG_CACHE_HOME/cmdop/<skill>/<key>.json  (default: ~/.cache/cmdop/...)
  - Windows: %LOCALAPPDATA%/cmdop/cache/<skill>/<key>.json

Usage::

    from cmdop_skill import SkillCache

    cache = SkillCache("my-skill")

    # Store a value for 1 hour
    cache.set("prompts", data, ttl=3600)

    # Retrieve (returns None if missing or expired)
    data = cache.get("prompts")

    # Check freshness
    if not cache.is_fresh("prompts", ttl=3600):
        data = fetch_fresh_data()
        cache.set("prompts", data, ttl=3600)
"""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Platform-aware cache root
# ---------------------------------------------------------------------------


def _get_cache_root() -> Path:
    """Return platform-specific cmdop skills cache root directory.

    Follows OS caching conventions (separate from config/persistent data):
      - macOS:   ~/Library/Caches/cmdop/skills/
      - Linux:   $XDG_CACHE_HOME/cmdop/skills/   (default: ~/.cache/cmdop/skills/)
      - Windows: %LOCALAPPDATA%/cmdop/cache/skills/
    """
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Caches" / "cmdop" / "skills"
    elif system == "Windows":
        local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local_appdata) / "cmdop" / "cache" / "skills"
    else:
        xdg = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
        return Path(xdg) / "cmdop" / "skills"


# ---------------------------------------------------------------------------
# Pydantic entry model
# ---------------------------------------------------------------------------


class CacheEntry(BaseModel, Generic[T]):
    """A single cached value with metadata."""

    key: str
    value: T
    created_at: datetime
    ttl: float | None  # seconds; None = never expires

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        age = (datetime.now(tz=timezone.utc) - self.created_at).total_seconds()
        return age > self.ttl

    @classmethod
    def create(cls, key: str, value: T, ttl: float | None) -> "CacheEntry[T]":
        return cls(
            key=key,
            value=value,
            created_at=datetime.now(tz=timezone.utc),
            ttl=ttl,
        )


# ---------------------------------------------------------------------------
# SkillCache
# ---------------------------------------------------------------------------


class SkillCache:
    """Disk-backed key/value cache scoped to a skill.

    Args:
        skill_name: Skill identifier used as the cache subdirectory name.
            Typically the package name (e.g. ``"prompts-chat"``).
        cache_root: Override the cache root directory (useful for testing).
    """

    def __init__(self, skill_name: str, *, cache_root: Path | None = None) -> None:
        self._skill_name = skill_name
        self._root = (cache_root or _get_cache_root()) / skill_name
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._root / f"{safe_key}.json"

    def _read_raw(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any | None:
        """Return cached value or ``None`` if missing or expired."""
        raw = self._read_raw(key)
        if raw is None:
            return None
        entry = CacheEntry[Any].model_validate(raw)
        if entry.is_expired:
            self._path(key).unlink(missing_ok=True)
            return None
        return entry.value

    def set(self, key: str, value: Any, *, ttl: float | None = None) -> None:
        """Store *value* under *key*.

        Args:
            key:   Cache key (alphanumeric + hyphens recommended).
            value: Any JSON-serializable value.
            ttl:   Time-to-live in seconds. ``None`` means the entry never expires.
        """
        entry = CacheEntry.create(key=key, value=value, ttl=ttl)
        self._path(key).write_text(
            entry.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )

    def delete(self, key: str) -> bool:
        """Remove a cached entry. Returns ``True`` if it existed."""
        path = self._path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Remove all entries for this skill. Returns number of deleted entries."""
        count = 0
        for path in self._root.glob("*.json"):
            try:
                path.unlink()
                count += 1
            except OSError:
                pass
        return count

    def is_fresh(self, key: str, *, ttl: float) -> bool:
        """Return ``True`` if *key* exists and is younger than *ttl* seconds."""
        raw = self._read_raw(key)
        if raw is None:
            return False
        try:
            entry = CacheEntry[Any].model_validate(raw)
            age = (datetime.now(tz=timezone.utc) - entry.created_at).total_seconds()
            return age <= ttl
        except Exception:
            return False

    def info(self, key: str) -> CacheEntry[Any] | None:
        """Return the full ``CacheEntry`` for inspection, or ``None`` if missing/expired."""
        raw = self._read_raw(key)
        if raw is None:
            return None
        entry = CacheEntry[Any].model_validate(raw)
        if entry.is_expired:
            self._path(key).unlink(missing_ok=True)
            return None
        return entry

    @property
    def cache_dir(self) -> Path:
        """The directory where this skill's cache files are stored."""
        return self._root
