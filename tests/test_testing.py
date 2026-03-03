"""Tests for the TestClient."""

from __future__ import annotations

import pytest

from cmdop_skill import Arg, Skill, TestClient


class TestTestClientRun:
    async def test_basic_run(self, client: TestClient) -> None:
        result = await client.run("greet", name="World")
        assert result["ok"] is True
        assert result["message"] == "Hello, World!"

    async def test_sync_command(self, client: TestClient) -> None:
        result = await client.run("ping")
        assert result["ok"] is True
        assert result["status"] == "pong"

    async def test_unknown_command(self, client: TestClient) -> None:
        result = await client.run("nonexistent")
        assert result["ok"] is False
        assert "Unknown command" in result["error"]

    async def test_handler_error(self) -> None:
        skill = Skill(name="err", auto_sys_path=False)

        @skill.command
        async def boom() -> dict:
            raise ValueError("kaboom")

        client = TestClient(skill)
        result = await client.run("boom")
        assert result["ok"] is False
        assert "kaboom" in result["error"]

    async def test_underscore_lookup(self, simple_skill: Skill) -> None:
        """Test that run() converts underscores to hyphens for lookup."""
        skill = Skill(name="test", auto_sys_path=False)

        @skill.command
        async def fetch_url(url: str = Arg(required=True)) -> dict:
            return {"url": url}

        client = TestClient(skill)
        result = await client.run("fetch_url", url="https://example.com")
        assert result["ok"] is True


class TestTestClientRunCli:
    async def test_cli_args(self, client: TestClient) -> None:
        result = await client.run_cli("greet", "--name", "CLI")
        assert result["ok"] is True
        assert result["message"] == "Hello, CLI!"

    async def test_cli_bad_args(self, client: TestClient) -> None:
        result = await client.run_cli("greet")  # missing required --name
        assert result["ok"] is False


class TestTestClientLifecycle:
    async def test_setup_runs_on_first_call(self, lifecycle_skill: Skill) -> None:
        client = TestClient(lifecycle_skill)
        result = await client.run("check")
        assert lifecycle_skill._state["setup"] is True  # type: ignore[attr-defined]

    async def test_context_manager(self, lifecycle_skill: Skill) -> None:
        async with TestClient(lifecycle_skill) as client:
            result = await client.run("check")
            assert result["ok"] is True
        assert lifecycle_skill._state["teardown"] is True  # type: ignore[attr-defined]

    async def test_explicit_teardown(self, lifecycle_skill: Skill) -> None:
        client = TestClient(lifecycle_skill)
        await client.setup()
        assert lifecycle_skill._state["setup"] is True  # type: ignore[attr-defined]
        await client.teardown()
        assert lifecycle_skill._state["teardown"] is True  # type: ignore[attr-defined]
