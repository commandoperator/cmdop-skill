"""Generate skill manifest from Skill metadata and command docstrings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmdop_skill._skill import Skill


def generate_manifest(skill: Skill) -> str:
    """Generate ``skill/config.py`` content from a Skill instance.

    Returns a Python source string that, when written to ``skill/config.py``,
    produces a valid SkillConfig-based manifest.
    """
    lines: list[str] = [
        "from cmdop_skill import SkillConfig",
        "",
        "config = SkillConfig(",
        f'    name="{skill.name}",',
        f'    version="{skill.version}",',
    ]

    if skill.description:
        lines.append(f'    description="{skill.description}",')

    lines.append(")")
    lines.append("")

    return "\n".join(lines)


def generate_readme(skill: Skill) -> str:
    """Generate ``skill/readme.md`` content from a Skill instance.

    Returns clean markdown (no YAML frontmatter) describing the skill
    and its commands.
    """
    lines: list[str] = []

    # Title
    lines.append(f"# {skill.name}")
    lines.append("")

    if skill.description:
        lines.append(skill.description)
        lines.append("")

    # Commands section
    if skill._commands:
        lines.append("## Commands")
        lines.append("")

        for cmd in skill._commands.values():
            lines.append(f"### `{cmd.name}`")
            lines.append("")

            if cmd.help:
                lines.append(cmd.help)
                lines.append("")

            if cmd.params:
                lines.append("| Argument | Type | Required | Default | Description |")
                lines.append("|----------|------|----------|---------|-------------|")

                for p in cmd.params:
                    type_name = getattr(p.annotation, "__name__", str(p.annotation))
                    required = "Yes" if p.required else "No"
                    default = str(p.default) if not p.required and p.default is not None else "-"
                    desc = p.help or "-"
                    lines.append(
                        f"| `{p.cli_name}` | {type_name} | {required} | {default} | {desc} |"
                    )

                lines.append("")

    return "\n".join(lines)
