"""CLI commands: publish, list."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from cmdop_skill._cli import app, console, err_console, _format_size, _resolve_api_key
from cmdop_skill._cli_auth import api_call_with_retry


@app.command()
def publish(
    path: Path = typer.Option(".", help="Skill directory"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="CMDOP_API_KEY"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    mode: str = typer.Option("prod", "--mode"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output for CI"),
) -> None:
    """Publish a skill to the CMDOP marketplace."""
    from cmdop_skill._publish import collect_skill_files, parse_skill_manifest, publish_skill

    resolved_path = Path(path).resolve()

    # Parse manifest and collect files
    try:
        manifest = parse_skill_manifest(resolved_path)
        files = collect_skill_files(resolved_path)
    except (FileNotFoundError, ValueError) as exc:
        if json_mode:
            print(json.dumps({"ok": False, "error": str(exc), "code": "VALIDATION_ERROR"}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    name = manifest["name"]
    version = manifest["version"]
    description = manifest.get("description", "")

    key = _resolve_api_key(api_key, json_mode)

    def _do_publish(k: str) -> dict:
        if not json_mode:
            with console.status("[bold green]Publishing...", spinner="dots"):
                return asyncio.run(
                    publish_skill(path=resolved_path, api_key=k, base_url=base_url, mode=mode)
                )
        else:
            return asyncio.run(
                publish_skill(path=resolved_path, api_key=k, base_url=base_url, mode=mode)
            )

    # JSON mode — skip wizard
    if json_mode:
        result = api_call_with_retry(_do_publish, key, json_mode)
        if result.get("ok"):
            from cmdop_skill.api.config import DASHBOARD_SKILLS_URL
            result["dashboard_url"] = DASHBOARD_SKILLS_URL
        print(json.dumps(result, indent=2, default=str))
        raise SystemExit(0 if result.get("ok") else 1)

    # Interactive wizard
    from importlib.metadata import version as pkg_version
    try:
        sdk_ver = pkg_version("cmdop-skill")
    except Exception:
        sdk_ver = "?"

    console.print()
    console.print(Panel.fit(
        f"[bold]Name:[/bold]        {name}\n"
        f"[bold]Version:[/bold]     {version}\n"
        f"[bold]Description:[/bold] {description or '[dim]—[/dim]'}\n"
        f"[dim]cmdop-skill {sdk_ver}[/dim]",
        title="[bold cyan]Skill Publish[/bold cyan]",
    ))

    # Files table
    table = Table(title=f"Files ({len(files)})", show_lines=False)
    table.add_column("Path", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Type")

    for f in files:
        ftype = "binary" if f.get("is_binary") else "text"
        table.add_row(f["path"], _format_size(f["size"]), ftype)

    console.print(table)
    console.print()

    if not Confirm.ask("  Publish?", default=False, console=console):
        console.print("[dim]Cancelled.[/dim]")
        raise SystemExit(0)

    result = api_call_with_retry(_do_publish, key, json_mode)

    if result.get("ok"):
        from cmdop_skill.api.config import DASHBOARD_SKILLS_URL

        console.print(
            f"  [bold green]\u2713[/bold green] Published {name} v{version} ({len(files)} files)"
        )
        console.print(
            f"  [dim]Dashboard:[/dim] [link={DASHBOARD_SKILLS_URL}]{DASHBOARD_SKILLS_URL}[/link]"
        )
    else:
        err_console.print(f"  [bold red]\u2717[/bold red] {result.get('error', 'Unknown error')}")
        raise SystemExit(1)


@app.command(name="list")
def list_skills(
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="CMDOP_API_KEY"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    mode: str = typer.Option("prod", "--mode"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output for CI"),
) -> None:
    """List your published skills."""
    from cmdop_skill.api.client import CMDOPSkillsAPI

    key = _resolve_api_key(api_key, json_mode)

    def _fetch(k: str) -> object:
        api_kwargs: dict[str, object] = {"api_key": k, "mode": mode}
        if base_url:
            api_kwargs["base_url"] = base_url

        async def _do() -> object:
            async with CMDOPSkillsAPI(**api_kwargs) as api:
                return await api.skills.my()

        return asyncio.run(_do())

    paginated = api_call_with_retry(_fetch, key, json_mode)
    skills = paginated.results  # type: ignore[union-attr]

    if json_mode:
        items = [
            {
                "name": s.name,
                "slug": s.slug,
                "status": str(s.status) if s.status else None,
                "install_count": s.install_count,
                "star_count": s.star_count,
            }
            for s in skills
        ]
        print(json.dumps({"ok": True, "skills": items}, indent=2))
        return

    console.print()
    table = Table(title=f"My Skills ({len(skills)})")
    table.add_column("Name", style="cyan")
    table.add_column("Status")
    table.add_column("Installs", justify="right")
    table.add_column("Stars", justify="right")

    for s in skills:
        status_str = str(s.status) if s.status else "\u2014"
        table.add_row(
            s.name,
            status_str,
            str(s.install_count),
            str(s.star_count),
        )

    console.print(table)
    console.print()
