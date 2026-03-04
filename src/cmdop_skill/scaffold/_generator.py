"""Render Jinja2 templates into a new skill directory."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader

from cmdop_skill.scaffold._models import ScaffoldConfig

# (template_file, output_path)  — {package_name} is replaced at runtime.
FILE_MAP: list[tuple[str, str]] = [
    ("pyproject.toml.j2", "pyproject.toml"),
    ("Makefile.j2", "Makefile"),
    ("README.md.j2", "README.md"),
    ("gitignore.j2", ".gitignore"),
    ("skill_config.py.j2", "skill/config.py"),
    ("skill_readme.md.j2", "skill/readme.md"),
    ("src_init.py.j2", "src/{package_name}/__init__.py"),
    ("conftest.py.j2", "tests/conftest.py"),
    ("test_placeholder.py.j2", "tests/test_{package_name}.py"),
]


def scaffold_skill(config: ScaffoldConfig, target_dir: Path) -> list[Path]:
    """Create a full skill directory tree from *config*.

    Args:
        config: Validated scaffold configuration.
        target_dir: Parent directory where ``config.name/`` will be created.

    Returns:
        List of created file paths.

    Raises:
        FileExistsError: If ``target_dir / config.name`` already exists.
    """
    root = target_dir / config.name
    if root.exists():
        raise FileExistsError(f"Directory already exists: {root}")

    env = Environment(
        loader=PackageLoader("cmdop_skill.scaffold", "templates"),
        keep_trailing_newline=True,
        autoescape=False,
    )

    # Template context — flat dict with all config fields + helpers.
    ctx = config.model_dump()
    # Enum → uppercase member name for the template (e.g. SECURITY).
    ctx["category_enum"] = config.category.name

    created: list[Path] = []
    for template_name, output_rel in FILE_MAP:
        output_rel = output_rel.replace("{package_name}", config.package_name)
        out_path = root / output_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        tmpl = env.get_template(template_name)
        out_path.write_text(tmpl.render(ctx), encoding="utf-8")
        created.append(out_path)

    return created
