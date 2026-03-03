"""
CMDOP Skills API Client.

Unified client for the CMDOP Skills marketplace API.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Literal

from cmdop_skill.api.config import get_base_url

if TYPE_CHECKING:
    from cmdop_skill.api.services.skills import SkillsService


class CMDOPSkillsAPI:
    """
    Unified CMDOP Skills API client.

    Provides access to the Skills marketplace API through a single interface.
    Uses lazy initialization for the service client.

    Example:
        >>> async with CMDOPSkillsAPI(api_key="cmd_xxx") as api:
        ...     skills = await api.skills.list()
        ...     skill = await api.skills.get("my-skill")

        >>> # With environment mode
        >>> api = CMDOPSkillsAPI(api_key="cmd_xxx", mode="dev")

        >>> # With custom base URL
        >>> api = CMDOPSkillsAPI(api_key="cmd_xxx", base_url="https://custom.api.com")

        >>> # From environment variable
        >>> os.environ["CMDOP_API_KEY"] = "cmd_xxx"
        >>> async with CMDOPSkillsAPI() as api:
        ...     skills = await api.skills.list()
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        mode: Literal["prod", "dev", "local"] = "prod",
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize CMDOP Skills API client.

        Args:
            api_key: API key (or set CMDOP_API_KEY env var)
            base_url: Custom base URL (overrides mode)
            mode: Environment mode - "prod", "dev", or "local"
            timeout: Request timeout in seconds

        Raises:
            ValueError: If no API key provided
        """
        self._api_key = api_key or os.environ.get("CMDOP_API_KEY")
        if not self._api_key:
            raise ValueError(
                "API key required. Pass api_key or set CMDOP_API_KEY environment variable."
            )

        self._base_url = base_url or get_base_url(mode)
        self._timeout = timeout
        self._mode = mode

        # Lazy-initialized
        self._skills_api: Any = None
        self._skills_service: SkillsService | None = None

    @property
    def skills(self) -> SkillsService:
        """
        Access skills API.

        Returns:
            SkillsService for skill marketplace operations
        """
        if self._skills_service is None:
            from cmdop_skill.api.generated import skills
            from cmdop_skill.api.services.skills import SkillsService

            self._skills_api = skills.API(self._base_url)
            self._skills_api.set_token(self._api_key)
            self._skills_service = SkillsService(self._skills_api)

        return self._skills_service

    @property
    def base_url(self) -> str:
        """Get current base URL."""
        return self._base_url

    @property
    def mode(self) -> str:
        """Get current environment mode."""
        return self._mode

    async def __aenter__(self) -> CMDOPSkillsAPI:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close all API clients."""
        if self._skills_api:
            await self._skills_api.close()

    def __repr__(self) -> str:
        return f"<CMDOPSkillsAPI base_url={self._base_url!r} mode={self._mode!r}>"


__all__ = ["CMDOPSkillsAPI"]
