"""Tests for test-scaffold-demo skill."""

from __future__ import annotations

import pytest

from cmdop_skill import TestClient

from test_scaffold_demo._skill import skill


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
