"""CLI commands: install, uninstall, run, test."""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer

from cmdop_skill._cli import app, console, err_console, _get_skills_dir, _resolve_api_key


@app.command()
def install(
    path: Path = typer.Argument(..., help="Path to skill directory"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Install a skill (symlink) into the system skills directory."""
    from cmdop_skill._publish import parse_skill_manifest

    resolved_path = Path(path).resolve()

    try:
        manifest = parse_skill_manifest(resolved_path)
    except (FileNotFoundError, ValueError) as exc:
        if json_mode:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    name = manifest["name"]
    skills_dir = _get_skills_dir()
    skills_dir.mkdir(parents=True, exist_ok=True)

    dst = skills_dir / name
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        elif dst.is_dir():
            shutil.rmtree(dst)

    dst.symlink_to(resolved_path)

    if json_mode:
        print(
            json.dumps(
                {"ok": True, "name": name, "path": str(resolved_path), "skills_dir": str(skills_dir)},
                indent=2,
            )
        )
    else:
        console.print(
            f"\n  [bold green]✓[/bold green] Installed {name} → {dst} (symlink)\n"
        )


@app.command()
def uninstall(
    name: str = typer.Argument(..., help="Skill name to uninstall"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Remove a skill from the system skills directory."""
    skills_dir = _get_skills_dir()
    dst = skills_dir / name

    if not dst.exists() and not dst.is_symlink():
        if json_mode:
            print(json.dumps({"ok": False, "error": f"Skill '{name}' not found in {skills_dir}"}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] Skill '{name}' not found in {skills_dir}")
        raise SystemExit(1)

    if dst.is_symlink() or dst.is_file():
        dst.unlink()
    elif dst.is_dir():
        shutil.rmtree(dst)

    if json_mode:
        print(json.dumps({"ok": True, "name": name}, indent=2))
    else:
        console.print(f"\n  [bold green]✓[/bold green] Uninstalled {name}\n")


@app.command()
def run(
    path: Path = typer.Argument(..., help="Path to skill directory"),
    prompt: str = typer.Argument(..., help="Prompt to run the skill with"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="CMDOP_API_KEY"),
    machine: Optional[str] = typer.Option(None, "--machine", help="Remote machine target"),
    model: Optional[str] = typer.Option(None, "--model", help="Model override"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Timeout in seconds"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Run a skill via the cmdop SDK."""
    from cmdop_skill._publish import parse_skill_manifest

    resolved_path = Path(path).resolve()

    try:
        manifest = parse_skill_manifest(resolved_path)
    except (FileNotFoundError, ValueError) as exc:
        if json_mode:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    name = manifest["name"]

    # Auto-install if not already installed
    skills_dir = _get_skills_dir()
    dst = skills_dir / name
    if not dst.exists():
        skills_dir.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(resolved_path)

    key = _resolve_api_key(api_key, json_mode)

    async def _run() -> object:
        from cmdop import AsyncCMDOPClient

        client_kwargs: dict[str, object] = {"api_key": key}
        async with AsyncCMDOPClient(**client_kwargs) as client:
            if machine:
                await client.set_machine(machine)

            run_opts: dict[str, object] = {}
            if model:
                run_opts["model"] = model
            if timeout:
                run_opts["timeout"] = timeout

            return await client.skills.run(name, prompt, **run_opts)

    start = time.monotonic()

    if not json_mode:
        with console.status(f"[bold green]Running {name}...", spinner="dots"):
            try:
                result = asyncio.run(_run())
            except Exception as exc:
                err_console.print(f"\n  [bold red]✗[/bold red] {exc}\n")
                raise SystemExit(1)
    else:
        try:
            result = asyncio.run(_run())
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            raise SystemExit(1)

    elapsed = time.monotonic() - start

    if json_mode:
        if hasattr(result, "model_dump"):
            print(json.dumps(result.model_dump(), indent=2, default=str))
        elif hasattr(result, "__dict__"):
            print(json.dumps(result.__dict__, indent=2, default=str))
        else:
            print(json.dumps({"ok": True, "result": str(result)}, indent=2))
    else:
        tokens = getattr(result, "total_tokens", None)
        tokens_str = f", {tokens} tokens" if tokens else ""
        console.print(f"  [bold green]✓[/bold green] Done ({elapsed:.1f}s{tokens_str})\n")

        text = getattr(result, "text", None) or getattr(result, "content", None) or str(result)
        console.print(text)
        console.print()


@app.command()
def test(
    path: Path = typer.Argument(".", help="Path to skill directory"),
    args: Optional[str] = typer.Option(None, "--args", "-a", help="Extra pytest args"),
) -> None:
    """Run pytest in a skill directory."""
    resolved_path = Path(path).resolve()

    skill_md = resolved_path / "skill.md"
    if not skill_md.exists():
        err_console.print(f"[red]Error:[/red] No skill.md found in {resolved_path}")
        raise SystemExit(1)

    name = resolved_path.name
    console.print(f"\n  Running tests in [bold]{name}[/bold]...\n")

    cmd = [sys.executable, "-m", "pytest"]
    if args:
        cmd.extend(args.split())

    result = subprocess.run(cmd, cwd=resolved_path)
    raise SystemExit(result.returncode)
