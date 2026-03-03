"""
CMDOP Skills API configuration.

Single source of truth for all URLs (API, dashboard, docs).
"""

from __future__ import annotations

from typing import Literal

# API base URLs
BASE_URLS = {
    "prod": "https://api.cmdop.com",
    "dev": "https://dev.cmdop.com",
    "local": "http://localhost:8000",
}

# Dashboard URLs
DASHBOARD_URL = "https://my.cmdop.com/dashboard"
DASHBOARD_SETTINGS_URL = f"{DASHBOARD_URL}/settings/"
DASHBOARD_SKILLS_URL = f"{DASHBOARD_URL}/skills/"


def get_base_url(mode: Literal["prod", "dev", "local"] = "prod") -> str:
    """Get API base URL for the specified environment."""
    return BASE_URLS.get(mode, BASE_URLS["prod"])


__all__ = [
    "get_base_url",
    "BASE_URLS",
    "DASHBOARD_URL",
    "DASHBOARD_SETTINGS_URL",
    "DASHBOARD_SKILLS_URL",
]
