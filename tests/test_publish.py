"""Tests for skill publish module — file collection and manifest parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from cmdop_skill._publish import (
    IGNORE_DIRS,
    IGNORE_FILE_PATTERNS,
    collect_skill_files,
    parse_skill_manifest,
)

SKILL_CONFIG_CONTENT = """\
from cmdop_skill import SkillConfig

config = SkillConfig(
    name="test-skill",
    version="1.0.0",
    description="A test skill",
)
"""

SKILL_README_CONTENT = """\
# test-skill

A test skill for unit tests.
"""


def _make_skill_dir(tmp_path: Path) -> Path:
    """Create skill/config.py + skill/readme.md in tmp_path."""
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "config.py").write_text(SKILL_CONFIG_CONTENT)
    (skill / "readme.md").write_text(SKILL_README_CONTENT)
    return tmp_path


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Create a minimal skill directory with skill/config.py."""
    _make_skill_dir(tmp_path)
    (tmp_path / "run.py").write_text("print('hello')\n")
    (tmp_path / "helpers.py").write_text("def helper(): pass\n")
    (tmp_path / "config.json").write_text('{"key": "value"}\n')
    return tmp_path


# ── collect_skill_files ─────────────────────────────────


class TestCollectSkillFiles:
    def test_collects_text_files(self, skill_dir: Path) -> None:
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert "skill/config.py" in paths
        assert "skill/readme.md" in paths
        assert "run.py" in paths
        assert "helpers.py" in paths
        assert "config.json" in paths

    def test_file_content_is_read(self, skill_dir: Path) -> None:
        files = collect_skill_files(skill_dir)
        by_path = {f["path"]: f for f in files}
        assert "print('hello')" in by_path["run.py"]["content"]

    def test_files_have_size(self, skill_dir: Path) -> None:
        files = collect_skill_files(skill_dir)
        for f in files:
            assert "size" in f
            assert isinstance(f["size"], int)
            assert f["size"] > 0

    def test_text_files_have_no_is_binary(self, skill_dir: Path) -> None:
        files = collect_skill_files(skill_dir)
        for f in files:
            assert "is_binary" not in f

    def test_binary_files_are_base64(self, skill_dir: Path) -> None:
        (skill_dir / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        files = collect_skill_files(skill_dir)
        by_path = {f["path"]: f for f in files}
        assert by_path["icon.png"]["is_binary"] is True
        # Should be valid base64
        import base64

        base64.b64decode(by_path["icon.png"]["content"])

    def test_raises_if_no_directory(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            collect_skill_files(tmp_path / "nonexistent")

    def test_raises_if_no_config(self, tmp_path: Path) -> None:
        (tmp_path / "run.py").write_text("pass\n")
        with pytest.raises(FileNotFoundError, match="skill/config.py"):
            collect_skill_files(tmp_path)

    def test_subdirectory_paths_are_relative(self, skill_dir: Path) -> None:
        sub = skill_dir / "lib"
        sub.mkdir()
        (sub / "utils.py").write_text("pass\n")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert "lib/utils.py" in paths


# ── ignore patterns ─────────────────────────────────────


class TestIgnorePatterns:
    def test_ignores_pycache(self, skill_dir: Path) -> None:
        cache = skill_dir / "__pycache__"
        cache.mkdir()
        (cache / "run.cpython-312.pyc").write_bytes(b"\x00")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert not any("__pycache__" in p for p in paths)

    def test_ignores_git(self, skill_dir: Path) -> None:
        git = skill_dir / ".git"
        git.mkdir()
        (git / "config").write_text("[core]\n")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert not any(".git" in p for p in paths)

    def test_ignores_data_dir(self, skill_dir: Path) -> None:
        data = skill_dir / "data"
        data.mkdir()
        (data / "cache.json").write_text("{}\n")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert not any(p.startswith("data/") for p in paths)

    def test_ignores_node_modules(self, skill_dir: Path) -> None:
        nm = skill_dir / "node_modules"
        nm.mkdir()
        (nm / "pkg.js").write_text("//\n")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert not any("node_modules" in p for p in paths)

    def test_ignores_ds_store(self, skill_dir: Path) -> None:
        (skill_dir / ".DS_Store").write_bytes(b"\x00")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert ".DS_Store" not in paths

    def test_ignores_pyc_files(self, skill_dir: Path) -> None:
        (skill_dir / "module.pyc").write_bytes(b"\x00")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert "module.pyc" not in paths

    def test_ignores_venv(self, skill_dir: Path) -> None:
        venv = skill_dir / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("home = /usr\n")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert not any(".venv" in p for p in paths)

    def test_ignores_db_files(self, skill_dir: Path) -> None:
        (skill_dir / "local.db").write_bytes(b"\x00")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert "local.db" not in paths

    def test_ignores_log_files(self, skill_dir: Path) -> None:
        (skill_dir / "debug.log").write_text("log line\n")
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert "debug.log" not in paths

    def test_all_ignore_dirs_documented(self) -> None:
        """Sanity check that the core dirs are in IGNORE_DIRS."""
        for d in ("__pycache__", ".git", "node_modules", "data", ".venv", "venv"):
            assert d in IGNORE_DIRS

    def test_all_ignore_file_patterns_documented(self) -> None:
        for pat in (".DS_Store", "*.pyc", "*.db", "*.log"):
            assert pat in IGNORE_FILE_PATTERNS


# ── parse_skill_manifest ────────────────────────────────


class TestParseSkillManifest:
    def test_parses_config_py(self, skill_dir: Path) -> None:
        result = parse_skill_manifest(skill_dir)
        assert result["name"] == "test-skill"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A test skill"

    def test_returns_default_fields(self, skill_dir: Path) -> None:
        result = parse_skill_manifest(skill_dir)
        assert result["requires"] == []
        assert result["tags"] == []

    def test_raises_if_no_config(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="skill/config.py"):
            parse_skill_manifest(tmp_path)

    def test_raises_if_no_config_var(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text("x = 1\n")
        with pytest.raises(ValueError, match="config"):
            parse_skill_manifest(tmp_path)

    def test_raises_on_invalid_config_type(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text("config = 'not a dict'\n")
        with pytest.raises(ValueError, match="SkillConfig instance or dict"):
            parse_skill_manifest(tmp_path)

    def test_accepts_dict_config(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text(
            'config = {"name": "dict-skill", "version": "0.1.0"}\n'
        )
        result = parse_skill_manifest(tmp_path)
        assert result["name"] == "dict-skill"
        assert result["version"] == "0.1.0"

    def test_validation_rejects_empty_name(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text(
            'from cmdop_skill import SkillConfig\n'
            'config = SkillConfig(name="", version="1.0.0")\n'
        )
        with pytest.raises(Exception):
            parse_skill_manifest(tmp_path)

    def test_backfills_from_pyproject(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text(
            'from cmdop_skill import SkillConfig\n'
            'config = SkillConfig(name="my-skill", version="1.0.0")\n'
        )
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "my-skill"\n'
            'version = "1.0.0"\n'
            'description = "From pyproject"\n'
            'keywords = ["net", "ssl"]\n'
            'dependencies = ["httpx"]\n'
            '\n'
            '[project.urls]\n'
            'Repository = "https://github.com/example/repo"\n'
        )
        result = parse_skill_manifest(tmp_path)
        assert result["short_description"] == "From pyproject"
        assert result["tags"] == ["net", "ssl"]
        assert result["requires"] == ["httpx"]
        assert result["repository_url"] == "https://github.com/example/repo"

    def test_config_wins_over_pyproject(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text(
            'from cmdop_skill import SkillConfig\n'
            'config = SkillConfig(\n'
            '    name="my-skill",\n'
            '    version="2.0.0",\n'
            '    description="From config",\n'
            '    tags=["config-tag"],\n'
            ')\n'
        )
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "my-skill"\n'
            'version = "1.0.0"\n'
            'description = "From pyproject"\n'
            'keywords = ["pyproject-tag"]\n'
        )
        result = parse_skill_manifest(tmp_path)
        assert result["version"] == "2.0.0"
        assert result["description"] == "From config"
        assert result["tags"] == ["config-tag"]

    def test_with_requires_and_tags(self, tmp_path: Path) -> None:
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "config.py").write_text(
            'from cmdop_skill import SkillConfig\n'
            'config = SkillConfig(\n'
            '    name="full-skill",\n'
            '    version="2.0.0",\n'
            '    description="Full featured",\n'
            '    requires=["httpx", "pydantic"],\n'
            '    tags=["network", "ssl"],\n'
            ')\n'
        )
        result = parse_skill_manifest(tmp_path)
        assert result["name"] == "full-skill"
        assert result["requires"] == ["httpx", "pydantic"]
        assert result["tags"] == ["network", "ssl"]
