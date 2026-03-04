"""Shared auth error handling with retry for CLI commands."""

from __future__ import annotations

import json
from typing import Callable, TypeVar

from rich.prompt import Prompt

from cmdop_skill.cli import err_console
from cmdop_skill.api.config import DASHBOARD_SETTINGS_URL as DASHBOARD_URL

T = TypeVar("T")


def is_auth_error(exc: Exception) -> bool:
    """Check if exception is an authentication/authorization error."""
    msg = str(exc).lower()
    if any(s in msg for s in ("401", "403", "unauthorized", "forbidden", "authentication")):
        return True
    status = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    return status in (401, 403)


def prompt_new_key() -> str:
    """Ask user for a new API key, showing dashboard link."""
    err_console.print(f"\n  Get your API key at: [link={DASHBOARD_URL}]{DASHBOARD_URL}[/link]\n")
    key = Prompt.ask("[bold]New API Key[/bold]", console=err_console)
    if not key:
        err_console.print("[red]API key is required.[/red]")
        raise SystemExit(1)
    return key


def api_call_with_retry(
    fn: Callable[[str], T],
    api_key: str,
    json_mode: bool,
) -> T:
    """Execute fn(api_key), retry once with new key on auth error.

    Args:
        fn: Callable that takes api_key and performs the API call.
        api_key: Current API key.
        json_mode: If True, output JSON errors and don't prompt.

    Returns:
        Result of fn().
    """
    from cmdop_skill._config import set_api_key

    try:
        return fn(api_key)
    except Exception as exc:
        if not is_auth_error(exc):
            if json_mode:
                print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            else:
                err_console.print(f"  [bold red]\u2717[/bold red] {exc}")
            raise SystemExit(1)

        # Auth error — prompt for new key (or fail in json mode)
        if json_mode:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": f"Authentication failed. Get your API key at {DASHBOARD_URL}",
                        "code": "AUTH_ERROR",
                    },
                    indent=2,
                )
            )
            raise SystemExit(1)

        err_console.print(f"\n  [red]Authentication failed:[/red] {exc}")
        err_console.print("  Your API key may be invalid or expired.")

        new_key = prompt_new_key()
        set_api_key(new_key)
        err_console.print("[dim]  New key saved.[/dim]\n")

        try:
            return fn(new_key)
        except Exception as exc2:
            err_console.print(f"  [bold red]\u2717[/bold red] {exc2}")
            raise SystemExit(1)
