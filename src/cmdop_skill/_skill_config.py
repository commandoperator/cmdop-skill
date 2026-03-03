"""SkillConfig — typed manifest for CMDOP skills.

Defines all fields needed to publish a skill to the marketplace::

    from cmdop_skill import SkillConfig

    config = SkillConfig(
        name="my-skill",
        version="1.0.0",
        description="Does useful things",
        tags=["network", "ssl"],
    )
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillConfig(BaseModel):
    """Typed skill manifest — maps 1:1 to the marketplace API.

    Attributes:
        name: Skill identifier (kebab-case, 1-150 chars). Used as slug.
        version: SemVer or CalVer string (1-20 chars).
        short_description: Brief summary for skill cards (max 300 chars).
        description: Full description with markdown support.
        category: Category slug on the marketplace.
        tags: Discovery tags for the marketplace.
        visibility: ``"public"`` or ``"private"``.
        repository_url: Link to source code repository.
        changelog: What changed in this version.
        requires: Runtime Python dependency list.
    """

    # ── required (version backfilled from pyproject.toml if omitted) ──
    name: str = Field(min_length=1, max_length=150)
    version: str = Field(default="", max_length=20)

    # ── skill metadata (API: skills.create / skills.update) ──
    short_description: str = Field(default="", max_length=300)
    description: str = ""
    category: str | None = None
    tags: list[str] = []
    visibility: Literal["public", "private"] | None = None
    repository_url: str | None = Field(default=None, max_length=200)

    # ── version metadata (API: skills.create_version) ──
    changelog: str | None = None

    # ── local-only (not sent to API) ──
    requires: list[str] = []
