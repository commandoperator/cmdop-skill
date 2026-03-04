#!/usr/bin/env python3
"""Scaffold a complete skill via Python API and verify it works.

Usage:
    python examples/scaffold_and_test.py                    # creates in examples/
    python examples/scaffold_and_test.py ./output            # creates in ./output
    python examples/scaffold_and_test.py --name my-tool      # custom name

The script:
  1. Scaffolds a new skill into the target directory (default: examples/)
  2. Adds a working _skill.py with a real command + run.py entry point
  3. Replaces placeholder test with a real TestClient-based test
  4. Patches pyproject.toml with [project.scripts] entry point
  5. Verifies all files + runs pytest
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Default: same directory as this script (examples/)
EXAMPLES_DIR = Path(__file__).resolve().parent

# ── Extra files that scaffold doesn't generate ────────

SKILL_PY = '''\
"""{{ name }} — CMDOP skill entry point."""

from __future__ import annotations

from cmdop_skill import Arg, Skill

skill = Skill(
    name="{{ name }}",
    description="{{ description }}",
    version="0.1.0",
)


@skill.command
def hello(
    name: str = Arg(help="Name to greet", required=True),
) -> dict:
    """Say hello."""
    return {"message": f"Hello, {name}!"}


def main() -> None:
    skill.run()


if __name__ == "__main__":
    main()
'''

RUN_PY = '''\
#!/usr/bin/env python3
"""CLI entry point for {{ name }} skill."""

from {{ package_name }}._skill import main

if __name__ == "__main__":
    main()
'''

TEST_REAL = '''\
"""Tests for {{ name }} skill."""

from __future__ import annotations

import pytest

from cmdop_skill import TestClient

from {{ package_name }}._skill import skill


@pytest.fixture
def client() -> TestClient:
    return TestClient(skill)


class TestHello:
    async def test_hello(self, client: TestClient) -> None:
        result = await client.run("hello", name="World")
        assert result["ok"] is True
        assert result["message"] == "Hello, World!"

    async def test_hello_cli(self, client: TestClient) -> None:
        result = await client.run_cli("hello", "--name", "CLI")
        assert result["ok"] is True
        assert result["message"] == "Hello, CLI!"
'''


def _render(template: str, **ctx: str) -> str:
    """Minimal {{ var }} renderer (no Jinja2 dependency needed)."""
    text = template
    for key, val in ctx.items():
        text = text.replace("{{ " + key + " }}", val)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold + test a CMDOP skill")
    parser.add_argument("target", nargs="?", default=None, help="Parent directory (default: examples/)")
    parser.add_argument("--name", default="test-scaffold-demo", help="Skill name (kebab-case)")
    args = parser.parse_args()

    # ── 1. Scaffold base structure ────────────────────────
    from cmdop_skill.scaffold import ScaffoldConfig, scaffold_skill

    config = ScaffoldConfig(
        name=args.name,
        description="Auto-generated demo skill for testing scaffold",
        category="testing",
        visibility="public",
        tags=["demo", "scaffold", "test"],
    )

    target = Path(args.target).resolve() if args.target else EXAMPLES_DIR
    target.mkdir(parents=True, exist_ok=True)

    skill_dir = target / config.name
    if skill_dir.exists():
        print(f"[cleanup] Removing existing {skill_dir}")
        shutil.rmtree(skill_dir)

    created = scaffold_skill(config, target)
    print(f"[scaffold] Created {len(created)} files in {skill_dir}")

    # ── 2. Add _skill.py + run.py ─────────────────────────
    ctx = {"name": config.name, "description": config.description, "package_name": config.package_name}

    skill_py_path = skill_dir / "src" / config.package_name / "_skill.py"
    skill_py_path.write_text(_render(SKILL_PY, **ctx), encoding="utf-8")

    run_py_path = skill_dir / "run.py"
    run_py_path.write_text(_render(RUN_PY, **ctx), encoding="utf-8")

    print(f"  + src/{config.package_name}/_skill.py")
    print("  + run.py")

    # ── 3. Replace placeholder test with real test ────────
    test_path = skill_dir / "tests" / f"test_{config.package_name}.py"
    test_path.write_text(_render(TEST_REAL, **ctx), encoding="utf-8")
    print(f"  ~ tests/test_{config.package_name}.py (replaced with real test)")

    # ── 4. Patch pyproject.toml — add [project.scripts] ───
    pyproject_path = skill_dir / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")

    scripts_section = (
        f"\n[project.scripts]\n"
        f'{config.name} = "{config.package_name}._skill:main"\n'
    )
    pyproject_text = pyproject_text.replace(
        "\n[project.urls]",
        f"{scripts_section}\n[project.urls]",
    )
    pyproject_path.write_text(pyproject_text, encoding="utf-8")
    print("  ~ pyproject.toml (added [project.scripts])")

    # ── 5. Verify files ───────────────────────────────────
    expected = [
        "pyproject.toml",
        "Makefile",
        "README.md",
        ".gitignore",
        "run.py",
        "skill/config.py",
        "skill/readme.md",
        f"src/{config.package_name}/__init__.py",
        f"src/{config.package_name}/_skill.py",
        "tests/conftest.py",
        f"tests/test_{config.package_name}.py",
    ]

    missing = [f for f in expected if not (skill_dir / f).is_file()]
    if missing:
        print(f"[FAIL] Missing files: {missing}")
        sys.exit(1)
    print(f"\n[verify] All {len(expected)} expected files present")

    # Content checks
    pyproject_text = pyproject_path.read_text()
    assert f'name = "{config.name}"' in pyproject_text
    assert "[project.scripts]" in pyproject_text
    assert "asyncio_mode" in pyproject_text
    print("[verify] pyproject.toml OK")

    skill_text = skill_py_path.read_text()
    assert "def hello(" in skill_text
    assert "skill.run()" in skill_text
    print("[verify] _skill.py OK")

    # ── 6. Run pytest ─────────────────────────────────────
    print(f"\n[test] Running pytest in {skill_dir}...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=skill_dir,
        env={**__import__("os").environ, "PYTHONPATH": str(skill_dir / "src")},
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("[FAIL] pytest failed")
        sys.exit(1)
    print("[test] pytest passed")

    # ── Done ──────────────────────────────────────────────
    print(f"[done] Skill at {skill_dir}")
    print("\n[OK] All checks passed!")


if __name__ == "__main__":
    main()
