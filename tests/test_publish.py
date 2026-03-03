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

SKILL_MD_CONTENT = """\
---
name: test-skill
version: 1.0.0
description: A test skill
---

# test-skill

A test skill for unit tests.
"""


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Create a minimal skill directory."""
    (tmp_path / "skill.md").write_text(SKILL_MD_CONTENT)
    (tmp_path / "run.py").write_text("print('hello')\n")
    (tmp_path / "helpers.py").write_text("def helper(): pass\n")
    (tmp_path / "config.json").write_text('{"key": "value"}\n')
    return tmp_path


# ── collect_skill_files ─────────────────────────────────


class TestCollectSkillFiles:
    def test_collects_text_files(self, skill_dir: Path) -> None:
        files = collect_skill_files(skill_dir)
        paths = {f["path"] for f in files}
        assert "skill.md" in paths
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

    def test_raises_if_no_skill_md(self, tmp_path: Path) -> None:
        (tmp_path / "run.py").write_text("pass\n")
        with pytest.raises(FileNotFoundError, match="skill.md"):
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
    def test_parses_basic_frontmatter(self, skill_dir: Path) -> None:
        result = parse_skill_manifest(skill_dir)
        assert result["name"] == "test-skill"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A test skill"

    def test_accepts_file_path_directly(self, skill_dir: Path) -> None:
        result = parse_skill_manifest(skill_dir / "skill.md")
        assert result["name"] == "test-skill"

    def test_raises_if_no_frontmatter(self, tmp_path: Path) -> None:
        (tmp_path / "skill.md").write_text("# No frontmatter\n")
        with pytest.raises(ValueError, match="missing YAML frontmatter"):
            parse_skill_manifest(tmp_path)

    def test_raises_if_no_name(self, tmp_path: Path) -> None:
        (tmp_path / "skill.md").write_text("---\nversion: 1.0.0\n---\n")
        with pytest.raises(ValueError, match="name"):
            parse_skill_manifest(tmp_path)

    def test_raises_if_no_version(self, tmp_path: Path) -> None:
        (tmp_path / "skill.md").write_text("---\nname: foo\n---\n")
        with pytest.raises(ValueError, match="version"):
            parse_skill_manifest(tmp_path)

    def test_raises_if_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            parse_skill_manifest(tmp_path)

    def test_ignores_comments_in_frontmatter(self, tmp_path: Path) -> None:
        (tmp_path / "skill.md").write_text(
            "---\nname: foo\n# comment\nversion: 2.0.0\n---\n"
        )
        result = parse_skill_manifest(tmp_path)
        assert result["name"] == "foo"
        assert result["version"] == "2.0.0"
        assert "#" not in result

    def test_extra_fields_preserved(self, tmp_path: Path) -> None:
        (tmp_path / "skill.md").write_text(
            "---\nname: foo\nversion: 1.0.0\nauthor: Alice\n---\n"
        )
        result = parse_skill_manifest(tmp_path)
        assert result["author"] == "Alice"
