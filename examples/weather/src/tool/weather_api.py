"""Fake weather API — simulates external service calls for demo purposes."""

from __future__ import annotations

import random

# In-memory "database" of queries
_history: list[dict] = []


async def init_cache() -> None:
    """Initialize the weather cache (setup hook demo)."""
    _history.clear()


async def close_cache() -> None:
    """Flush and close the cache (teardown hook demo)."""
    _history.clear()


async def get_forecast(city: str, days: int, units: str) -> dict:
    """Return a fake weather forecast."""
    forecast = []
    for i in range(days):
        temp = random.randint(-5, 35) if units == "metric" else random.randint(20, 95)
        forecast.append({
            "day": i + 1,
            "temp": temp,
            "units": "°C" if units == "metric" else "°F",
            "condition": random.choice(["sunny", "cloudy", "rainy", "snowy", "windy"]),
        })

    result = {"city": city, "days": days, "forecast": forecast}
    _history.append({"type": "forecast", "city": city})
    return result


async def get_alerts(region: str, severity: str) -> dict:
    """Return fake weather alerts for a region."""
    alerts = []
    if severity in ("warning", "all"):
        alerts.append({
            "type": "warning",
            "message": f"Strong winds expected in {region}",
            "expires": "2026-03-05T18:00:00Z",
        })
    if severity in ("watch", "all"):
        alerts.append({
            "type": "watch",
            "message": f"Frost advisory for {region}",
            "expires": "2026-03-06T06:00:00Z",
        })

    _history.append({"type": "alerts", "region": region})
    return {"region": region, "alerts": alerts, "count": len(alerts)}


def check_api_health() -> dict:
    """Sync health check — demonstrates sync command support."""
    return {"ok": True, "status": "operational", "api_version": "2.1"}


async def get_history() -> dict:
    """Return query history."""
    return {"queries": list(_history), "total": len(_history)}
