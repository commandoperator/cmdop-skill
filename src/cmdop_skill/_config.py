"""Global API key storage — cmdop/configs/apikey.json."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path


def _get_cmdop_dir() -> Path:
    """Platform-specific cmdop root directory."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "cmdop"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "cmdop"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg) / "cmdop"


def _get_apikey_path() -> Path:
    return _get_cmdop_dir() / "configs" / "apikey.json"


def get_api_key() -> str | None:
    """Get saved API key from cmdop/configs/apikey.json."""
    path = _get_apikey_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("api_key")
    except (json.JSONDecodeError, OSError):
        return None


def set_api_key(key: str) -> None:
    """Save API key to cmdop/configs/apikey.json."""
    path = _get_apikey_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": key}, indent=2) + "\n", encoding="utf-8")


def clear_api_key() -> None:
    """Remove API key file."""
    path = _get_apikey_path()
    if path.exists():
        path.unlink()


def get_apikey_path() -> Path:
    """Public accessor for display purposes."""
    return _get_apikey_path()
