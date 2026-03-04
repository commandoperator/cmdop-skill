"""CLI command: ``cmdop-skill init`` — scaffold a new skill."""

from __future__ import annotations

from pathlib import Path

import typer

from cmdop_skill.cli import app, console, err_console


@app.command()
def init(
    path: Path = typer.Argument(
        ".",
        help="Parent directory where the skill folder will be created",
    ),
) -> None:
    """Create a new CMDOP skill project (interactive wizard)."""
    from cmdop_skill.scaffold._generator import scaffold_skill
    from cmdop_skill.scaffold._wizard import run_wizard

    config = run_wizard(console)
    if config is None:
        raise SystemExit(0)

    target = Path(path).resolve()
    try:
        created = scaffold_skill(config, target)
    except FileExistsError as exc:
        err_console.print(f"  [red]Error:[/red] {exc}")
        raise SystemExit(1)

    console.print(
        f"\n  [bold green]✓[/bold green] Created [bold]{config.name}[/bold] "
        f"({len(created)} files)\n"
    )

    skill_dir = target / config.name
    console.print("  [bold]Next steps:[/bold]")
    console.print(f"    cd {skill_dir.name}")
    console.print("    pip install -e '.[dev]'")
    console.print("    make test")
    console.print()
