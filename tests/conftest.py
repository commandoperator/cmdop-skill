"""Shared fixtures for cmdop_skill tests."""

from __future__ import annotations

import pytest

from cmdop_skill import Arg, Skill, TestClient


@pytest.fixture
def simple_skill() -> Skill:
    """A minimal skill with one sync and one async command."""
    skill = Skill(name="test-skill", description="Test skill", version="1.0.0", auto_sys_path=False)

    @skill.command
    async def greet(name: str = Arg(help="Who to greet", required=True)) -> dict:
        """Say hello."""
        return {"message": f"Hello, {name}!"}

    @skill.command
    def ping() -> dict:
        """Health check."""
        return {"status": "pong"}

    return skill


@pytest.fixture
def lifecycle_skill() -> Skill:
    """A skill with setup and teardown hooks."""
    skill = Skill(name="lifecycle-skill", description="Has lifecycle", version="0.1.0", auto_sys_path=False)
    skill._state: dict = {"setup": False, "teardown": False}  # type: ignore[attr-defined]

    @skill.setup
    async def setup():
        skill._state["setup"] = True  # type: ignore[attr-defined]

    @skill.teardown
    async def teardown():
        skill._state["teardown"] = True  # type: ignore[attr-defined]

    @skill.command
    async def check() -> dict:
        """Return state."""
        return {"state": skill._state}  # type: ignore[attr-defined]

    return skill


@pytest.fixture
def client(simple_skill: Skill) -> TestClient:
    """TestClient wrapping simple_skill."""
    return TestClient(simple_skill)
