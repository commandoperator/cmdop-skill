"""Interactive Rich wizard that collects input and returns a ScaffoldConfig."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from cmdop_skill._pypi import check_pypi_name
from cmdop_skill._skill_config import SkillCategory
from cmdop_skill.scaffold._models import ScaffoldConfig

# Ordered list of categories for the selection table.
_CATEGORIES: list[tuple[int, SkillCategory]] = list(enumerate(SkillCategory, start=1))


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
            console.print(f"  [green]✓[/green] [bold]{name}[/bold] is available on PyPI")
        else:
            console.print(
                f"  [yellow]⚠[/yellow] [bold]{name}[/bold] is already taken on PyPI "
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


def _ask_category(console: Console) -> SkillCategory:
    """Show category table and prompt for selection."""
    table = Table(title="Categories", show_header=False, box=None, padding=(0, 2))
    table.add_column("N", style="dim", width=4)
    table.add_column("Slug", width=16)
    table.add_column("N", style="dim", width=4)
    table.add_column("Slug", width=16)

    # Two-column layout.
    half = (len(_CATEGORIES) + 1) // 2
    for i in range(half):
        left_n, left_cat = _CATEGORIES[i]
        row = [str(left_n), left_cat.value]
        if i + half < len(_CATEGORIES):
            right_n, right_cat = _CATEGORIES[i + half]
            row += [str(right_n), right_cat.value]
        else:
            row += ["", ""]
        table.add_row(*row)

    console.print()
    console.print(table)

    while True:
        choice = Prompt.ask(
            "  [bold]Category[/bold] (number or slug)",
            default=str(SkillCategory.OTHER.value),
            console=console,
        ).strip()

        # Try as number.
        try:
            idx = int(choice)
            if 1 <= idx <= len(_CATEGORIES):
                return _CATEGORIES[idx - 1][1]
        except ValueError:
            pass

        # Try as slug.
        for _, cat in _CATEGORIES:
            if cat.value == choice:
                return cat

        console.print(f"  [red]Invalid choice: {choice!r}[/red]")


def _ask_visibility(console: Console) -> str:
    """Prompt for visibility."""
    return Prompt.ask(
        "  [bold]Visibility[/bold]",
        choices=["public", "private"],
        default="public",
        console=console,
    )


def _ask_tags(console: Console) -> list[str]:
    """Prompt for comma-separated tags."""
    raw = Prompt.ask(
        "  [bold]Tags[/bold] (comma-separated, optional)",
        default="",
        console=console,
    ).strip()
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


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
            "[bold]Create a new CMDOP skill[/bold]",
            subtitle="cmdop-skill init",
            style="cyan",
        )
    )

    name = _ask_name(console)
    description = _ask_description(console)
    category = _ask_category(console)
    visibility = _ask_visibility(console)
    tags = _ask_tags(console)
    author_name, author_email = _ask_author(console)

    config = ScaffoldConfig(
        name=name,
        description=description,
        category=category,
        visibility=visibility,
        tags=tags,
        author_name=author_name,
        author_email=author_email,
    )

    # Summary panel.
    summary = (
        f"  [bold]Name:[/bold]        {config.name}\n"
        f"  [bold]Package:[/bold]     {config.package_name}\n"
        f"  [bold]Description:[/bold] {config.description or '(none)'}\n"
        f"  [bold]Category:[/bold]    {config.category.value}\n"
        f"  [bold]Visibility:[/bold]  {config.visibility}\n"
        f"  [bold]Tags:[/bold]        {', '.join(config.tags) or '(none)'}\n"
        f"  [bold]Author:[/bold]      {config.author_name} <{config.author_email}>"
    )
    console.print()
    console.print(Panel(summary, title="Summary", style="green"))

    if not Confirm.ask("\n  Create skill?", default=True, console=console):
        console.print("  [dim]Cancelled.[/dim]")
        return None

    return config
