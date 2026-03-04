"""
Skills service for CMDOP Skills API.

Provides high-level interface for skill marketplace operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmdop_skill.api.generated.skills import API as SkillsAPI
    from cmdop_skill.api.generated.skills.skills__api__skills.models import (
        PaginatedSkillListList,
        PaginatedSkillReviewList,
        PatchedSkillUpdateRequest,
        SkillCategory,
        SkillCreate,
        SkillDetail,
        SkillInstall,
        SkillStar,
        SkillTag,
        SkillUpdate,
        SkillVersion,
    )
    from cmdop_skill.api.generated.skills.enums import (
        PatchedSkillUpdateRequestStatus,
        PatchedSkillUpdateRequestVisibility,
    )


class SkillsService:
    """
    High-level skills service.

    Wraps the generated skills API with convenient methods.

    Example:
        >>> async with SkillsAPI(api_key="cmd_xxx") as api:
        ...     skills = await api.skills.list()
        ...     skill = await api.skills.get("my-skill")
        ...     await api.skills.star("my-skill")
    """

    def __init__(self, api: SkillsAPI) -> None:
        self._api = api
        self._client = api.skills_skills

    # ── Browse ─────────────────────────────────────────────

    async def list(
        self,
        category: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
    ) -> PaginatedSkillListList:
        """List published skills with optional filtering."""
        return await self._client.skills_list(
            category=category,
            tag=tag,
            search=search,
            page=page,
            page_size=page_size,
            ordering=ordering,
        )

    async def get(self, slug: str) -> SkillDetail:
        """Get skill details by slug."""
        return await self._client.skills_retrieve(slug=slug)

    async def my(
        self,
        search: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
    ) -> PaginatedSkillListList:
        """List current user's skills (including private and draft)."""
        return await self._client.skills_my_list(
            search=search,
            page=page,
            page_size=page_size,
            ordering=ordering,
        )

    # ── CRUD ───────────────────────────────────────────────

    async def create(
        self,
        name: str,
        short_description: str = "",
        description: str = "",
        category: str | None = None,
        tags: list[str] | None = None,
        visibility: PatchedSkillUpdateRequestVisibility | str | None = None,
        repository_url: str | None = None,
    ) -> SkillCreate:
        """Create a new skill."""
        from cmdop_skill.api.generated.skills.skills__api__skills.models import (
            SkillCreateRequest,
        )

        data = SkillCreateRequest(
            name=name,
            short_description=short_description,
            description=description,
            category=category,
            tags=tags if tags else None,
            visibility=visibility,
            repository_url=repository_url,
        )
        return await self._client.skills_create(data=data)

    async def update(
        self,
        slug: str,
        **kwargs,
    ) -> SkillUpdate:
        """Partially update a skill by slug."""
        from cmdop_skill.api.generated.skills.skills__api__skills.models import (
            PatchedSkillUpdateRequest,
        )

        data = PatchedSkillUpdateRequest(**kwargs)
        return await self._client.skills_partial_update(slug=slug, data=data)

    async def delete(self, slug: str) -> None:
        """Delete a skill by slug."""
        await self._client.skills_destroy(slug=slug)

    # ── Actions ────────────────────────────────────────────

    async def star(self, slug: str) -> SkillStar:
        """Toggle star on a skill. Returns new state."""
        return await self._client.skills_star_create(slug=slug)

    async def install(self, slug: str) -> SkillInstall:
        """Install a skill. Returns files and package dependencies."""
        return await self._client.skills_install_create(slug=slug)

    # ── Versions ───────────────────────────────────────────

    async def list_versions(self, slug: str) -> list[SkillVersion]:
        """List all versions of a skill."""
        return await self._client.skills_versions_list(slug=slug)

    async def create_version(
        self,
        slug: str,
        version: str,
        files: list[dict],
        changelog: str | None = None,
    ) -> SkillVersion:
        """Publish a new version of a skill."""
        from cmdop_skill.api.generated.skills.skills__api__skills.models import (
            SkillVersionCreateRequest,
        )

        data = SkillVersionCreateRequest(
            version=version,
            files=files,
            changelog=changelog if changelog else None,
        )
        return await self._client.skills_versions_create_create(slug=slug, data=data)

    async def publish(
        self,
        slug: str,
        raw_manifest: str,
        skill_md: str | None = None,
        readme: str | None = None,
        changelog: str | None = None,
    ) -> SkillVersion:
        """Publish via LLM-powered parsing + translations.

        Sends raw manifest text to Django — server parses it,
        creates version, and translates descriptions.
        """
        from cmdop_skill.api.generated.skills.skills__api__skills.models import (
            SkillPublishRequest,
        )

        data = SkillPublishRequest(
            raw_manifest=raw_manifest,
            skill_md=skill_md,
            readme=readme,
            changelog=changelog,
        )
        return await self._client.skills_publish_create(slug=slug, data=data)

    # ── Reviews ────────────────────────────────────────────

    async def list_reviews(
        self,
        slug: str,
        page: int | None = None,
        page_size: int | None = None,
    ) -> PaginatedSkillReviewList:
        """List reviews for a skill."""
        return await self._client.skills_reviews_list(
            slug=slug,
            page=page,
            page_size=page_size,
        )

    # ── Categories & Tags ──────────────────────────────────

    async def list_categories(self) -> list[SkillCategory]:
        """List all skill categories."""
        return await self._client.categories_list()

    async def list_tags(self) -> list[SkillTag]:
        """List all skill tags."""
        return await self._client.tags_list()
