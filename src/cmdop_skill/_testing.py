"""TestClient for programmatic invocation of skills in tests."""

from __future__ import annotations

import inspect
from typing import Any

from cmdop_skill._output import format_error, wrap_result
from cmdop_skill._skill import Skill


class TestClient:
    """Test client that invokes skill commands without sys.exit or stdout capture.

    Usage::

        client = TestClient(skill)
        result = await client.run("send", to="x@y.com", subject="Hi", body="Hello")
        assert result["ok"] is True
    """

    def __init__(self, skill: Skill) -> None:
        self.skill = skill
        self._setup_done = False

    async def setup(self) -> None:
        """Run all setup hooks."""
        for hook in self.skill._setup_hooks:
            await hook()
        self._setup_done = True

    async def teardown(self) -> None:
        """Run all teardown hooks."""
        for hook in self.skill._teardown_hooks:
            await hook()
        self._setup_done = False

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Invoke a command by name with keyword arguments.

        Runs setup hooks on first call. Returns the result dict directly.
        """
        if not self._setup_done:
            await self.setup()

        cmd = self.skill._commands.get(command)
        if cmd is None:
            # Try underscore variant
            cmd = self.skill._commands.get(command.replace("_", "-"))
        if cmd is None:
            return format_error(KeyError(f"Unknown command: {command}"))

        try:
            handler = cmd.handler
            if inspect.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)
            return wrap_result(result)
        except Exception as exc:
            return format_error(exc)

    async def run_cli(self, *args: str) -> dict[str, Any]:
        """Invoke a command via CLI argument strings.

        Example::

            result = await client.run_cli("send", "--to", "x@y.com", "--subject", "Hi", "--body", "Hello")
        """
        if not self._setup_done:
            await self.setup()

        try:
            ns = self.skill.parse_args(list(args))
        except SystemExit:
            return format_error(SystemExit("Argument parsing failed"))

        try:
            return await self.skill.dispatch(ns)
        except Exception as exc:
            return format_error(exc)

    async def __aenter__(self) -> TestClient:
        await self.setup()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.teardown()
