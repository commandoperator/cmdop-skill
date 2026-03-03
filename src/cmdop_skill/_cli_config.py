"""CLI commands: config set-key, config show, config reset."""

from __future__ import annotations

import typer
from rich.prompt import Prompt

from cmdop_skill._cli import app, console, err_console
from cmdop_skill._config import clear_api_key, get_api_key, get_apikey_path, set_api_key

config_app = typer.Typer(help="Manage global configuration")
app.add_typer(config_app, name="config")


@config_app.command(name="set-key")
def set_key(
    key: str = typer.Argument(None, help="API key (omit to enter interactively)"),
) -> None:
    """Save API key globally."""
    if not key:
        key = Prompt.ask("[bold]API Key[/bold]", console=err_console)
    if not key:
        err_console.print("[red]API key is required.[/red]")
        raise SystemExit(1)

    set_api_key(key)
    console.print(f"  [bold green]\u2713[/bold green] API key saved to {get_apikey_path()}")


@config_app.command(name="show")
def show() -> None:
    """Show current config (key masked)."""
    key = get_api_key()
    if key:
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        console.print(f"  api_key: {masked}")
    else:
        console.print("  [dim]No API key configured[/dim]")
    console.print(f"  path:    {get_apikey_path()}")


@config_app.command(name="reset")
def reset() -> None:
    """Remove saved API key."""
    clear_api_key()
    console.print("  [bold green]\u2713[/bold green] API key removed")
