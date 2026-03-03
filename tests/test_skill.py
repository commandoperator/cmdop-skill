"""Tests for the Skill class."""

from __future__ import annotations

import pytest

from cmdop_skill import Arg, Skill


class TestSkillRegistration:
    def test_command_registration(self, simple_skill: Skill) -> None:
        assert "greet" in simple_skill._commands
        assert "ping" in simple_skill._commands

    def test_underscore_to_hyphen_name(self) -> None:
        skill = Skill(name="test", auto_sys_path=False)

        @skill.command
        async def fetch_url() -> dict:
            return {}

        assert "fetch-url" in skill._commands

    def test_command_help_from_docstring(self, simple_skill: Skill) -> None:
        assert simple_skill._commands["greet"].help == "Say hello."
        assert simple_skill._commands["ping"].help == "Health check."

    def test_setup_registration(self, lifecycle_skill: Skill) -> None:
        assert len(lifecycle_skill._setup_hooks) == 1

    def test_teardown_registration(self, lifecycle_skill: Skill) -> None:
        assert len(lifecycle_skill._teardown_hooks) == 1


class TestSkillParser:
    def test_build_parser(self, simple_skill: Skill) -> None:
        parser = simple_skill.build_parser()
        ns = parser.parse_args(["greet", "--name", "World"])
        assert ns.command == "greet"
        assert ns.name == "World"

    def test_parse_args(self, simple_skill: Skill) -> None:
        ns = simple_skill.parse_args(["ping"])
        assert ns.command == "ping"

    def test_missing_command_exits(self, simple_skill: Skill) -> None:
        with pytest.raises(SystemExit):
            simple_skill.parse_args([])


class TestSkillDispatch:
    async def test_async_command(self, simple_skill: Skill) -> None:
        ns = simple_skill.parse_args(["greet", "--name", "World"])
        result = await simple_skill.dispatch(ns)
        assert result["ok"] is True
        assert result["message"] == "Hello, World!"

    async def test_sync_command(self, simple_skill: Skill) -> None:
        ns = simple_skill.parse_args(["ping"])
        result = await simple_skill.dispatch(ns)
        assert result["ok"] is True
        assert result["status"] == "pong"

    async def test_result_with_ok_passthrough(self) -> None:
        skill = Skill(name="test", auto_sys_path=False)

        @skill.command
        async def check() -> dict:
            return {"ok": False, "error": "nope"}

        ns = skill.parse_args(["check"])
        result = await skill.dispatch(ns)
        assert result["ok"] is False
        assert result["error"] == "nope"


class TestSkillMetadata:
    def test_name(self, simple_skill: Skill) -> None:
        assert simple_skill.name == "test-skill"

    def test_version(self, simple_skill: Skill) -> None:
        assert simple_skill.version == "1.0.0"

    def test_description(self, simple_skill: Skill) -> None:
        assert simple_skill.description == "Test skill"
