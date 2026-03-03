"""CLI entry point for cmdop-skill — Typer + Rich."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

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
    """Resolve API key: flag -> env -> interactive prompt."""
    key = api_key or os.environ.get("CMDOP_API_KEY")
    if key:
        return key

    if json_mode:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "API key required. Use --api-key or set CMDOP_API_KEY env var.",
                    "code": "AUTH_REQUIRED",
                },
                indent=2,
            )
        )
        raise SystemExit(1)

    key = Prompt.ask("[bold]API Key[/bold]", password=True, console=err_console)
    if not key:
        err_console.print("[red]API key is required.[/red]")
        raise SystemExit(1)
    return key


# Register command modules (side-effect imports)
import cmdop_skill._cli_dev as _cli_dev  # noqa: E402, F401
import cmdop_skill._cli_publish as _cli_publish  # noqa: E402, F401


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point for cmdop-skill."""
    app(argv)


if __name__ == "__main__":
    main()
