"""Tests for the scaffold subpackage — models, generator, wizard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cmdop_skill._skill_config import SkillCategory
from cmdop_skill.scaffold._generator import FILE_MAP, scaffold_skill
from cmdop_skill.scaffold._models import ScaffoldConfig


# ── ScaffoldConfig model ───────────────────────────────


class TestScaffoldConfigValidation:
    def test_valid_kebab_name(self) -> None:
        cfg = ScaffoldConfig(name="my-cool-skill")
        assert cfg.name == "my-cool-skill"

    def test_single_word_name(self) -> None:
        cfg = ScaffoldConfig(name="checker")
        assert cfg.name == "checker"

    def test_name_with_digits(self) -> None:
        cfg = ScaffoldConfig(name="ssl-cert-checker-2")
        assert cfg.name == "ssl-cert-checker-2"

    def test_name_uppercased_is_lowered(self) -> None:
        cfg = ScaffoldConfig(name="My-Skill")
        assert cfg.name == "my-skill"

    def test_rejects_underscore_name(self) -> None:
        with pytest.raises(ValueError, match="kebab-case"):
            ScaffoldConfig(name="my_skill")

    def test_rejects_space_in_name(self) -> None:
        with pytest.raises(ValueError, match="kebab-case"):
            ScaffoldConfig(name="my skill")

    def test_rejects_trailing_hyphen(self) -> None:
        with pytest.raises(ValueError, match="kebab-case"):
            ScaffoldConfig(name="my-skill-")

    def test_rejects_leading_hyphen(self) -> None:
        with pytest.raises(ValueError, match="kebab-case"):
            ScaffoldConfig(name="-my-skill")

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ValueError):
            ScaffoldConfig(name="")

    def test_rejects_too_long_name(self) -> None:
        with pytest.raises(ValueError):
            ScaffoldConfig(name="a" * 151)


class TestScaffoldConfigDefaults:
    def test_default_description(self) -> None:
        cfg = ScaffoldConfig(name="test")
        assert cfg.description == ""

    def test_default_author(self) -> None:
        cfg = ScaffoldConfig(name="test")
        assert cfg.author_name == "CMDOP Team"
        assert cfg.author_email == "team@cmdop.com"

    def test_default_category(self) -> None:
        cfg = ScaffoldConfig(name="test")
        assert cfg.category == SkillCategory.OTHER

    def test_default_visibility(self) -> None:
        cfg = ScaffoldConfig(name="test")
        assert cfg.visibility == "public"

    def test_default_tags(self) -> None:
        cfg = ScaffoldConfig(name="test")
        assert cfg.tags == []


class TestScaffoldConfigPackageName:
    def test_derived_from_name(self) -> None:
        cfg = ScaffoldConfig(name="my-cool-skill")
        assert cfg.package_name == "my_cool_skill"

    def test_single_word(self) -> None:
        cfg = ScaffoldConfig(name="checker")
        assert cfg.package_name == "checker"

    def test_explicit_override(self) -> None:
        cfg = ScaffoldConfig(name="my-skill", package_name="custom_pkg")
        assert cfg.package_name == "custom_pkg"


class TestScaffoldConfigTags:
    def test_comma_string_parsed(self) -> None:
        cfg = ScaffoldConfig(name="test", tags="web, api, ssl")  # type: ignore[arg-type]
        assert cfg.tags == ["web", "api", "ssl"]

    def test_empty_string_gives_empty_list(self) -> None:
        cfg = ScaffoldConfig(name="test", tags="")  # type: ignore[arg-type]
        assert cfg.tags == []

    def test_list_passthrough(self) -> None:
        cfg = ScaffoldConfig(name="test", tags=["a", "b"])
        assert cfg.tags == ["a", "b"]

    def test_strips_whitespace(self) -> None:
        cfg = ScaffoldConfig(name="test", tags=" net , ssl ")  # type: ignore[arg-type]
        assert cfg.tags == ["net", "ssl"]


class TestScaffoldConfigCategory:
    def test_enum_value(self) -> None:
        cfg = ScaffoldConfig(name="test", category=SkillCategory.SECURITY)
        assert cfg.category == SkillCategory.SECURITY

    def test_string_coercion(self) -> None:
        cfg = ScaffoldConfig(name="test", category="security")  # type: ignore[arg-type]
        assert cfg.category == SkillCategory.SECURITY


# ── scaffold_skill generator ──────────────────────────


class TestScaffoldSkill:
    @pytest.fixture
    def config(self) -> ScaffoldConfig:
        return ScaffoldConfig(
            name="demo-skill",
            description="A demo",
            category=SkillCategory.TESTING,
            visibility="public",
            tags=["demo", "test"],
            author_name="Test Author",
            author_email="test@example.com",
        )

    def test_creates_correct_number_of_files(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        created = scaffold_skill(config, tmp_path)
        assert len(created) == len(FILE_MAP)

    def test_creates_skill_directory(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        assert (tmp_path / "demo-skill").is_dir()

    def test_raises_if_dir_exists(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        (tmp_path / "demo-skill").mkdir()
        with pytest.raises(FileExistsError, match="already exists"):
            scaffold_skill(config, tmp_path)

    def test_expected_files_exist(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        root = tmp_path / "demo-skill"
        assert (root / "pyproject.toml").is_file()
        assert (root / "Makefile").is_file()
        assert (root / "README.md").is_file()
        assert (root / ".gitignore").is_file()
        assert (root / "skill" / "config.py").is_file()
        assert (root / "skill" / "readme.md").is_file()
        assert (root / "src" / "demo_skill" / "__init__.py").is_file()
        assert (root / "tests" / "conftest.py").is_file()
        assert (root / "tests" / "test_demo_skill.py").is_file()

    def test_pyproject_contains_name(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "pyproject.toml").read_text()
        assert 'name = "demo-skill"' in text
        assert 'description = "A demo"' in text
        assert '"demo",' in text
        assert '"test",' in text

    def test_skill_config_has_category(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "skill" / "config.py").read_text()
        assert "SkillCategory.TESTING" in text
        assert 'name="demo-skill"' in text
        assert 'visibility="public"' in text

    def test_src_init_has_docstring(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "src" / "demo_skill" / "__init__.py").read_text()
        assert "demo-skill" in text

    def test_test_placeholder_passes(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "tests" / "test_demo_skill.py").read_text()
        assert "def test_placeholder" in text
        assert "assert True" in text

    def test_makefile_has_targets(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "Makefile").read_text()
        assert "install:" in text
        assert "test:" in text
        assert "lint:" in text
        assert "release:" in text

    def test_gitignore_has_patterns(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / ".gitignore").read_text()
        assert "__pycache__/" in text
        assert ".venv/" in text

    def test_returns_absolute_paths(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        created = scaffold_skill(config, tmp_path)
        for p in created:
            assert p.is_absolute()
            assert p.is_file()

    def test_author_in_pyproject(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "pyproject.toml").read_text()
        assert "Test Author" in text
        assert "test@example.com" in text

    def test_hatch_packages_path(self, tmp_path: Path, config: ScaffoldConfig) -> None:
        scaffold_skill(config, tmp_path)
        text = (tmp_path / "demo-skill" / "pyproject.toml").read_text()
        assert 'packages = ["src/demo_skill"]' in text


# ── wizard (unit-level, mocked IO) ────────────────────


class TestWizard:
    @patch("cmdop_skill.scaffold._wizard.check_pypi_name")
    @patch("cmdop_skill.scaffold._wizard.Confirm.ask")
    @patch("cmdop_skill.scaffold._wizard.Prompt.ask")
    def test_full_flow_returns_config(
        self, mock_prompt: MagicMock, mock_confirm: MagicMock, mock_pypi: MagicMock
    ) -> None:
        from cmdop_skill.scaffold._wizard import run_wizard

        # Simulate user answers in order:
        # name, description, category (number), visibility, tags, author_name, author_email
        mock_prompt.side_effect = [
            "my-wizard-skill",   # name
            "A wizard test",     # description
            "20",                # category = other
            "public",            # visibility
            "tag1, tag2",        # tags
            "Author",            # author_name
            "a@b.com",           # author_email
        ]
        mock_confirm.side_effect = [True]  # "Create skill?"
        mock_pypi.return_value = {"available": True, "name": "my-wizard-skill"}

        console = MagicMock()
        console.status.return_value.__enter__ = MagicMock()
        console.status.return_value.__exit__ = MagicMock()

        config = run_wizard(console)

        assert config is not None
        assert config.name == "my-wizard-skill"
        assert config.description == "A wizard test"
        assert config.package_name == "my_wizard_skill"
        assert config.tags == ["tag1", "tag2"]

    @patch("cmdop_skill.scaffold._wizard.check_pypi_name")
    @patch("cmdop_skill.scaffold._wizard.Confirm.ask")
    @patch("cmdop_skill.scaffold._wizard.Prompt.ask")
    def test_cancel_returns_none(
        self, mock_prompt: MagicMock, mock_confirm: MagicMock, mock_pypi: MagicMock
    ) -> None:
        from cmdop_skill.scaffold._wizard import run_wizard

        mock_prompt.side_effect = [
            "cancel-skill",
            "desc",
            "20",
            "public",
            "",
            "Author",
            "a@b.com",
        ]
        mock_confirm.side_effect = [False]  # cancel
        mock_pypi.return_value = {"available": True, "name": "cancel-skill"}

        console = MagicMock()
        console.status.return_value.__enter__ = MagicMock()
        console.status.return_value.__exit__ = MagicMock()

        result = run_wizard(console)
        assert result is None
