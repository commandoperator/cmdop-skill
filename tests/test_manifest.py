"""Tests for manifest generation."""

from __future__ import annotations

from cmdop_skill import Arg, Skill, generate_manifest
from cmdop_skill._manifest import generate_readme


class TestGenerateManifest:
    def test_basic_manifest(self) -> None:
        skill = Skill(name="my-skill", description="Does things", version="1.0.0", auto_sys_path=False)

        result = generate_manifest(skill)

        assert 'from cmdop_skill import SkillConfig' in result
        assert 'name="my-skill"' in result
        assert 'version="1.0.0"' in result
        assert 'description="Does things"' in result

    def test_no_description(self) -> None:
        skill = Skill(name="empty", version="0.0.1", auto_sys_path=False)
        result = generate_manifest(skill)
        assert 'name="empty"' in result
        assert "description" not in result


class TestGenerateReadme:
    def test_basic_readme(self) -> None:
        skill = Skill(name="my-skill", description="Does things", version="1.0.0", auto_sys_path=False)

        @skill.command
        async def greet(name: str = Arg(help="Who to greet", required=True)) -> dict:
            """Say hello."""
            return {}

        md = generate_readme(skill)

        assert "# my-skill" in md
        assert "Does things" in md
        assert "## Commands" in md
        assert "### `greet`" in md
        assert "Say hello." in md
        assert "| `--name` |" in md
        assert "| Yes |" in md
        # No YAML frontmatter
        assert not md.startswith("---")

    def test_multiple_commands(self) -> None:
        skill = Skill(name="multi", version="2.0.0", auto_sys_path=False)

        @skill.command
        async def send() -> dict:
            """Send something."""
            return {}

        @skill.command
        async def receive() -> dict:
            """Receive something."""
            return {}

        md = generate_readme(skill)
        assert "### `send`" in md
        assert "### `receive`" in md

    def test_no_commands(self) -> None:
        skill = Skill(name="empty", version="0.0.1", auto_sys_path=False)
        md = generate_readme(skill)
        assert "# empty" in md
        assert "## Commands" not in md

    def test_param_table(self) -> None:
        skill = Skill(name="test", version="1.0.0", auto_sys_path=False)

        @skill.command
        async def fetch(
            url: str = Arg(help="URL to fetch", required=True),
            limit: int = Arg(help="Max results", default=10),
        ) -> dict:
            return {}

        md = generate_readme(skill)
        assert "| Argument | Type | Required | Default | Description |" in md
        assert "| `--url` | str | Yes |" in md
        assert "| `--limit` | int | No | 10 | Max results |" in md
