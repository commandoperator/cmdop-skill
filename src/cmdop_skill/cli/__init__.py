"""CLI entry point for cmdop-skill — Typer + Rich."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="cmdop-skill",
    help="CMDOP Skill CLI — publish and manage skills",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def _get_skills_dir() -> Path:
    """Detect platform-specific skills directory."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "cmdop" / "skills"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "cmdop" / "skills"
    else:
        xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        return Path(xdg) / "cmdop" / "skills"


def _format_size(size: int) -> str:
    """Format byte size to human-readable string."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    else:
        return f"{size / (1024 * 1024):.1f}MB"


def _resolve_api_key(api_key: str | None, json_mode: bool) -> str:
    """Resolve API key: flag -> env -> saved config -> interactive prompt."""
    from cmdop_skill.cli._auth import DASHBOARD_URL, prompt_new_key
    from cmdop_skill._config import get_api_key, set_api_key

    key = api_key or os.environ.get("CMDOP_API_KEY") or get_api_key()
    if key:
        return key

    if json_mode:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"API key required. Use --api-key, set CMDOP_API_KEY, or run: cmdop-skill config set-key. Get key at {DASHBOARD_URL}",
                    "code": "AUTH_REQUIRED",
                },
                indent=2,
            )
        )
        raise SystemExit(1)

    key = prompt_new_key()

    # Save for future use
    set_api_key(key)
    err_console.print("[dim]  Key saved. Use 'cmdop-skill config set-key' to change.[/dim]")
    return key


# Register command modules (side-effect imports)
import cmdop_skill.cli._config_cmd as _config_cmd  # noqa: E402, F401
import cmdop_skill.cli._dev as _dev  # noqa: E402, F401
import cmdop_skill.cli._init_cmd as _init_cmd  # noqa: E402, F401
import cmdop_skill.cli._release as _release  # noqa: E402, F401
import cmdop_skill.cli._publish_cmd as _publish_cmd  # noqa: E402, F401


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point for cmdop-skill."""
    app(argv)


if __name__ == "__main__":
    main()
