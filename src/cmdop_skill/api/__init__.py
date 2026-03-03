"""
CMDOP Skills SDK API Client.

Provides unified access to the CMDOP Skills marketplace API.

Usage:
    >>> from cmdop_skill.api import CMDOPSkillsAPI
    >>>
    >>> async with CMDOPSkillsAPI(api_key="cmd_xxx") as api:
    ...     skills = await api.skills.list()
    ...     skill = await api.skills.get("my-skill")

For direct access to generated clients:
    >>> from cmdop_skill.api.generated import skills
"""

from __future__ import annotations

from cmdop_skill.api.client import CMDOPSkillsAPI
from cmdop_skill.api.config import get_base_url, BASE_URLS
from cmdop_skill.api.services import SkillsService

__all__ = [
    "CMDOPSkillsAPI",
    "get_base_url",
    "BASE_URLS",
    "SkillsService",
]
