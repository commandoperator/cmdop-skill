"""CLI commands: install, uninstall, run, test, bump, check-name, release."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer

from cmdop_skill._cli import app, console, err_console, _get_skills_dir, _resolve_api_key
from cmdop_skill._cli_auth import api_call_with_retry


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

    async def _run(api_key: str) -> object:
        from cmdop import AsyncCMDOPClient

        client_kwargs: dict[str, object] = {"api_key": api_key}
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

    def _execute(k: str) -> object:
        if not json_mode:
            with console.status(f"[bold green]Running {name}...", spinner="dots"):
                return asyncio.run(_run(k))
        else:
            return asyncio.run(_run(k))

    result = api_call_with_retry(lambda k: _execute(k), key, json_mode)

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

    from cmdop_skill._publish import _has_skill_manifest

    if not _has_skill_manifest(resolved_path):
        err_console.print(
            f"[red]Error:[/red] No skill/config.py found in {resolved_path}"
        )
        raise SystemExit(1)

    name = resolved_path.name
    console.print(f"\n  Running tests in [bold]{name}[/bold]...\n")

    cmd = [sys.executable, "-m", "pytest"]
    if args:
        cmd.extend(args.split())

    result = subprocess.run(cmd, cwd=resolved_path)
    raise SystemExit(result.returncode)


# ── version bump ─────────────────────────────────────────


def _bump_semver(current: str, part: str) -> str:
    """Bump a semver string by part (patch/minor/major).

    Handles both 3-segment (1.2.3) and 4-segment (2026.3.4.1) versions.
    """
    segments = [int(s) for s in current.split(".")]

    # Pad to at least 3 segments
    while len(segments) < 3:
        segments.append(0)

    if part == "major":
        segments[0] += 1
        segments[1:] = [0] * (len(segments) - 1)
    elif part == "minor":
        segments[1] += 1
        segments[2:] = [0] * (len(segments) - 2)
    else:  # patch
        segments[2] += 1
        segments[3:] = []

    return ".".join(str(s) for s in segments)


def _bump_pyproject(pyproject: Path, new_version: str) -> None:
    """Rewrite version in pyproject.toml."""
    text = pyproject.read_text(encoding="utf-8")
    text = re.sub(
        r'(version\s*=\s*["\'])([^"\']+)(["\'])',
        rf"\g<1>{new_version}\g<3>",
        text,
        count=1,
    )
    pyproject.write_text(text, encoding="utf-8")


@app.command()
def bump(
    path: Path = typer.Argument(".", help="Path to skill directory"),
    major: bool = typer.Option(False, "--major", help="Bump major version"),
    minor: bool = typer.Option(False, "--minor", help="Bump minor version"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Bump version in pyproject.toml (semver: patch by default)."""
    from cmdop_skill._publish import parse_skill_manifest

    resolved_path = Path(path).resolve()
    pyproject = resolved_path / "pyproject.toml"

    if not pyproject.is_file():
        if json_mode:
            print(json.dumps({"ok": False, "error": "pyproject.toml not found"}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] pyproject.toml not found in {resolved_path}")
        raise SystemExit(1)

    try:
        manifest = parse_skill_manifest(resolved_path)
    except (FileNotFoundError, ValueError) as exc:
        if json_mode:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    part = "major" if major else "minor" if minor else "patch"
    name = manifest["name"]
    old_version = manifest.get("version", "0.0.0")
    new_version = _bump_semver(old_version, part)
    _bump_pyproject(pyproject, new_version)

    if json_mode:
        print(json.dumps({
            "ok": True, "name": name, "part": part,
            "old_version": old_version, "new_version": new_version,
        }, indent=2))
    else:
        console.print(
            f"\n  [bold green]✓[/bold green] {name}: {old_version} → {new_version} ({part})\n"
        )


@app.command(name="check-name")
def check_name(
    name: str = typer.Argument(..., help="Package name to check"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Check if a package name is available on PyPI."""
    from cmdop_skill._pypi import check_pypi_name

    with console.status(f"[bold green]Checking {name}...", spinner="dots"):
        result = check_pypi_name(name)

    if json_mode:
        print(json.dumps(result, indent=2, default=str))
        return

    if result.get("error"):
        err_console.print(f"  [red]Error:[/red] {result['error']}")
        raise SystemExit(1)

    if result["available"]:
        console.print(f"\n  [bold green]✓[/bold green] [bold]{name}[/bold] is available on PyPI\n")
    else:
        console.print(f"\n  [bold red]✗[/bold red] [bold]{name}[/bold] is taken on PyPI")
        if result.get("version"):
            console.print(f"  [dim]v{result['version']}[/dim]  {result.get('summary', '')}")
        if result.get("url"):
            console.print(f"  [dim]{result['url']}[/dim]")
        console.print()


@app.command()
def release(
    path: Path = typer.Argument(".", help="Path to skill directory"),
    part: str = typer.Option("patch", "--bump", "-b", help="Version bump: patch/minor/major"),
    test_pypi: bool = typer.Option(False, "--test-pypi", help="Upload to TestPyPI"),
    no_bump: bool = typer.Option(False, "--no-bump", help="Skip version bump"),
    no_publish: bool = typer.Option(False, "--no-publish", help="Skip CMDOP marketplace publish"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="CMDOP_API_KEY"),
    json_mode: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Bump version, build, upload to PyPI, and publish to CMDOP marketplace."""
    from rich.prompt import Confirm

    from cmdop_skill._publish import collect_skill_files, parse_skill_manifest, publish_skill
    from cmdop_skill._pypi import (
        build as pypi_build, clean, dist_files, upload,
        inject_readme_badge, patch_pyproject_urls,
    )

    resolved_path = Path(path).resolve()
    pyproject = resolved_path / "pyproject.toml"

    if not pyproject.is_file():
        if json_mode:
            print(json.dumps({"ok": False, "error": "pyproject.toml not found"}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] pyproject.toml not found in {resolved_path}")
        raise SystemExit(1)

    try:
        manifest = parse_skill_manifest(resolved_path)
    except (FileNotFoundError, ValueError) as exc:
        if json_mode:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            err_console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    name = manifest["name"]
    old_version = manifest.get("version", "0.0.0")

    # Bump
    if no_bump:
        new_version = old_version
    else:
        if part not in ("patch", "minor", "major"):
            if json_mode:
                print(json.dumps({"ok": False, "error": f"Invalid bump part: {part}"}, indent=2))
            else:
                err_console.print(f"[red]Error:[/red] Invalid bump part: {part}")
            raise SystemExit(1)
        new_version = _bump_semver(old_version, part)
        _bump_pyproject(pyproject, new_version)

    target = "TestPyPI" if test_pypi else "PyPI"
    do_publish = not no_publish and not test_pypi

    # Inject CMDOP badge into README and patch pyproject.toml URLs
    inject_readme_badge(resolved_path, name)
    patch_pyproject_urls(resolved_path, name)

    # JSON mode — no wizard
    if json_mode:
        clean(resolved_path)
        ok, err = pypi_build(resolved_path)
        if not ok:
            print(json.dumps({"ok": False, "error": f"Build failed: {err}"}, indent=2))
            raise SystemExit(1)

        ok, out = upload(resolved_path, test_pypi=test_pypi)
        result: dict[str, object] = {
            "ok": ok,
            "name": name,
            "version": new_version,
            "target": target,
            "files": [{"name": n, "size": s} for n, s in dist_files(resolved_path)],
        }
        if not ok:
            result["error"] = out
            print(json.dumps(result, indent=2, default=str))
            raise SystemExit(1)

        # CMDOP marketplace publish
        if do_publish:
            key = _resolve_api_key(api_key, json_mode)
            try:
                # Re-parse manifest to pick up bumped version
                pub_result = asyncio.run(
                    publish_skill(path=resolved_path, api_key=key)
                )
                result["marketplace"] = pub_result
            except Exception as exc:
                result["marketplace_error"] = str(exc)

            from cmdop_skill.api.config import DASHBOARD_SKILLS_URL
            result["dashboard_url"] = DASHBOARD_SKILLS_URL

        print(json.dumps(result, indent=2, default=str))
        raise SystemExit(0)

    # Interactive
    bump_str = f"{old_version} → {new_version}" if not no_bump else f"{old_version} (no bump)"
    targets = target + (" + CMDOP" if do_publish else "")
    console.print(f"\n  [bold]{name}[/bold]  {bump_str}  →  {targets}\n")

    if not Confirm.ask("  Release?", default=False, console=console):
        if not no_bump and new_version != old_version:
            _bump_pyproject(pyproject, old_version)  # rollback
        console.print("[dim]Cancelled.[/dim]")
        raise SystemExit(0)

    # Clean + Build
    with console.status("[bold green]Building...", spinner="dots"):
        clean(resolved_path)
        ok, err = pypi_build(resolved_path)

    if not ok:
        err_console.print(f"  [bold red]✗[/bold red] Build failed\n{err}")
        raise SystemExit(1)

    for fname, fsize in dist_files(resolved_path):
        console.print(f"  [cyan]{fname}[/cyan] ({fsize / 1024:.1f} KB)")

    # Upload to PyPI
    with console.status(f"[bold green]Uploading to {target}...", spinner="dots"):
        ok, out = upload(resolved_path, test_pypi=test_pypi)

    if not ok:
        err_console.print(f"  [bold red]✗[/bold red] Upload failed\n{out}")
        raise SystemExit(1)

    pypi_url = "https://test.pypi.org" if test_pypi else "https://pypi.org"
    console.print(f"  [bold green]✓[/bold green] {name} v{new_version} → {target}")
    console.print(f"  [dim]{pypi_url}/project/{name}/[/dim]")

    # Publish to CMDOP marketplace
    if do_publish:
        key = _resolve_api_key(api_key, json_mode)

        def _do_publish(k: str) -> dict:
            return asyncio.run(publish_skill(path=resolved_path, api_key=k))

        with console.status("[bold green]Publishing to CMDOP...", spinner="dots"):
            pub_result = api_call_with_retry(_do_publish, key, json_mode)

        if pub_result.get("ok"):
            from cmdop_skill.api.config import DASHBOARD_SKILLS_URL

            files = collect_skill_files(resolved_path)
            console.print(
                f"  [bold green]✓[/bold green] {name} v{new_version} → CMDOP ({len(files)} files)"
            )
            console.print(
                f"  [dim]{DASHBOARD_SKILLS_URL}[/dim]"
            )
        else:
            err_console.print(
                f"  [bold red]✗[/bold red] CMDOP publish failed: {pub_result.get('error', '?')}"
            )
            err_console.print("  [dim]PyPI upload succeeded. Run 'cmdop-skill publish' to retry.[/dim]")

    console.print()
