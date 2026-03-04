"""SkillConfig — typed manifest for CMDOP skills.

Minimal config for ``skill/config.py``. Category, tags, and visibility
are determined automatically by the server during publish::

    from cmdop_skill import SkillConfig

    config = SkillConfig()  # name, version from pyproject.toml

``name``, ``version``, and ``description`` are auto-resolved from ``pyproject.toml``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


# Keep SkillCategory importable for backwards compat, but it's no longer needed
try:
    from cmdop_skill.api.generated.skills.enums import (
        PatchedSkillUpdateRequestCategory as SkillCategory,
    )
except ImportError:
    SkillCategory = None  # type: ignore[assignment,misc]


class SkillConfig(BaseModel):
    """Typed skill manifest.

    Only ``name`` and ``version`` are required (auto-resolved from pyproject.toml).
    Category, tags, visibility, and repository_url are determined
    automatically by the server during publish from the manifest keywords.

    Attributes:
        name: Skill identifier (kebab-case). Auto-resolved from pyproject.toml.
        version: SemVer or CalVer string. Auto-resolved from pyproject.toml.
        short_description: Brief summary for skill cards (max 300 chars).
        description: Full description with markdown support.
        changelog: What changed in this version.
        requires: Runtime dependency list (local-only, not sent to API).
    """

    # ── auto-resolved from pyproject.toml when empty ──
    name: str = Field(default="", max_length=150)
    version: str = Field(default="", max_length=20)

    # ── skill metadata ──
    short_description: str = Field(default="", max_length=300)
    description: str = ""

    # ── version metadata ──
    changelog: str | None = None

    # ── local-only (not sent to API) ──
    requires: list[str] = []

    @model_validator(mode="after")
    def _fill_from_pyproject(self) -> SkillConfig:
        """Backfill empty name/version/description from pyproject.toml."""
        if not self.name or not self.version or not self.description:
            from cmdop_skill._resolve import resolve_project_meta

            meta = resolve_project_meta()
            if not self.name:
                self.name = meta.get("name", "")
            if not self.version:
                self.version = meta.get("version", "")
            if not self.description:
                self.description = meta.get("description", "")
            if not self.short_description and self.description:
                self.short_description = self.description[:300]
        return self
