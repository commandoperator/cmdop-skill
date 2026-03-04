"""Interactive Rich wizard that collects input and returns a ScaffoldConfig."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from cmdop_skill._pypi import check_pypi_name
from cmdop_skill.scaffold._models import ScaffoldConfig


def _ask_name(console: Console) -> str:
    """Prompt for skill name and check PyPI availability."""
    while True:
        name = Prompt.ask(
            "\n  [bold]Skill name[/bold] (kebab-case)",
            console=console,
        ).strip().lower()

        if not name:
            console.print("  [red]Name is required.[/red]")
            continue

        # Quick local validation before hitting PyPI.
        try:
            ScaffoldConfig.model_validate({"name": name})
        except Exception as exc:
            console.print(f"  [red]{exc}[/red]")
            continue

        # Check PyPI
        with console.status("  Checking PyPI...", spinner="dots"):
            result = check_pypi_name(name)

        if result.get("error"):
            console.print(f"  [yellow]PyPI check failed:[/yellow] {result['error']}")
        elif result["available"]:
            console.print(f"  [green]\u2713[/green] [bold]{name}[/bold] is available on PyPI")
        else:
            console.print(
                f"  [yellow]\u26a0[/yellow] [bold]{name}[/bold] is already taken on PyPI "
                f"(v{result.get('version', '?')})"
            )
            if not Confirm.ask("  Use this name anyway?", default=False, console=console):
                continue

        return name


def _ask_description(console: Console) -> str:
    """Prompt for short description."""
    return Prompt.ask(
        "  [bold]Description[/bold] (optional, max 300 chars)",
        default="",
        console=console,
    ).strip()[:300]


def _ask_author(console: Console) -> tuple[str, str]:
    """Prompt for author name and email."""
    name = Prompt.ask(
        "  [bold]Author name[/bold]",
        default="CMDOP Team",
        console=console,
    ).strip()
    email = Prompt.ask(
        "  [bold]Author email[/bold]",
        default="team@cmdop.com",
        console=console,
    ).strip()
    return name, email


def run_wizard(console: Console) -> ScaffoldConfig | None:
    """Run the interactive scaffold wizard.

    Returns:
        A validated ``ScaffoldConfig``, or ``None`` if cancelled.
    """
    console.print(
        Panel(
            "[bold]Create a new CMDOP skill[/bold]\n"
            "[dim]Category, tags, and visibility are auto-determined during publish.[/dim]",
            subtitle="cmdop-skill init",
            style="cyan",
        )
    )

    name = _ask_name(console)
    description = _ask_description(console)
    author_name, author_email = _ask_author(console)

    config = ScaffoldConfig(
        name=name,
        description=description,
        author_name=author_name,
        author_email=author_email,
    )

    # Summary panel.
    summary = (
        f"  [bold]Name:[/bold]        {config.name}\n"
        f"  [bold]Package:[/bold]     {config.package_name}\n"
        f"  [bold]Description:[/bold] {config.description or '(none)'}\n"
        f"  [bold]Author:[/bold]      {config.author_name} <{config.author_email}>"
    )
    console.print()
    console.print(Panel(summary, title="Summary", style="green"))

    if not Confirm.ask("\n  Create skill?", default=True, console=console):
        console.print("  [dim]Cancelled.[/dim]")
        return None

    return config
