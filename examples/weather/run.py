#!/usr/bin/env python3
"""
weather — demo CMDOP skill showing all cmdop_skill framework features.

Demonstrates:
  - @skill.setup / @skill.teardown lifecycle hooks
  - Async and sync commands
  - Arg() with: required, default, choices, --flag aliases, bool flags
  - Underscore-to-hyphen command naming (get_alerts → get-alerts)
  - Auto sys.path setup (src/ directory)
  - JSON output wrapping (dict without "ok" gets wrapped automatically)

Usage:
  python run.py forecast --city Moscow --days 3
  python run.py forecast --city NYC --days 7 --units imperial
  python run.py get-alerts --region California --severity all
  python run.py health
  python run.py history
"""

from cmdop_skill import Skill, Arg

skill = Skill(
    name="weather",
    description="Weather forecasts and alerts (demo skill)",
    version="1.0.0",
)


# ── Lifecycle ──────────────────────────────────────────────

@skill.setup
async def setup():
    from tool.weather_api import init_cache
    await init_cache()


@skill.teardown
async def teardown():
    from tool.weather_api import close_cache
    await close_cache()


# ── Commands ───────────────────────────────────────────────

@skill.command
async def forecast(
    city: str = Arg(help="City name", required=True),
    days: int = Arg(help="Number of days (1-14)", default=5),
    units: str = Arg(help="Temperature units", choices=("metric", "imperial"), default="metric"),
) -> dict:
    """Get weather forecast for a city."""
    from tool.weather_api import get_forecast
    return await get_forecast(city=city, days=days, units=units)


@skill.command
async def get_alerts(
    region: str = Arg(help="Region or state name", required=True),
    severity: str = Arg(help="Filter by severity", choices=("warning", "watch", "all"), default="all"),
) -> dict:
    """Get active weather alerts for a region."""
    from tool.weather_api import get_alerts
    return await get_alerts(region=region, severity=severity)


@skill.command
def health() -> dict:
    """Check weather API health status."""
    from tool.weather_api import check_api_health
    return check_api_health()


@skill.command
async def history() -> dict:
    """Show recent query history."""
    from tool.weather_api import get_history
    return await get_history()


if __name__ == "__main__":
    skill.run()
