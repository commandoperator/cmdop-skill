"""Skill class — the main entry point for defining CMDOP skills."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import sys
from typing import Any, Callable, TypeVar

from cmdop_skill._output import format_error, wrap_result
from cmdop_skill._parser import CommandInfo, build_subparser, extract_params
from cmdop_skill._types import LifecycleHook

F = TypeVar("F", bound=Callable[..., Any])


class Skill:
    """Decorator-based framework for building CMDOP skill CLIs.

    Usage::

        skill = Skill(name="my-skill", description="Does things", version="1.0.0")

        @skill.command
        async def hello(name: str = Arg(help="Who to greet")) -> dict:
            return {"greeting": f"Hello, {name}!"}

        if __name__ == "__main__":
            skill.run()
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "0.0.0",
        *,
        auto_sys_path: bool = True,
    ) -> None:
        self.name = name
        self.description = description
        self.version = version
        self._commands: dict[str, CommandInfo] = {}
        self._setup_hooks: list[LifecycleHook] = []
        self._teardown_hooks: list[LifecycleHook] = []

        if auto_sys_path:
            self._setup_sys_path()

    # -- Decorators --

    def command(self, func: F) -> F:
        """Register an async or sync function as a CLI subcommand.

        The function name (with ``_`` replaced by ``-``) becomes the subcommand name.
        The first line of the docstring becomes the help text.
        """
        cmd_name = func.__name__.replace("_", "-")
        help_text = _first_line(func.__doc__) if func.__doc__ else ""
        params = extract_params(func)
        self._commands[cmd_name] = CommandInfo(
            name=cmd_name,
            handler=func,
            help=help_text,
            params=params,
        )
        return func

    def setup(self, func: F) -> F:
        """Register an async lifecycle setup hook."""
        self._setup_hooks.append(func)  # type: ignore[arg-type]
        return func

    def teardown(self, func: F) -> F:
        """Register an async lifecycle teardown hook."""
        self._teardown_hooks.append(func)  # type: ignore[arg-type]
        return func

    # -- Parser --

    def build_parser(self) -> argparse.ArgumentParser:
        """Build the full argparse parser from registered commands."""
        parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.description,
        )
        parser.add_argument("--version", action="version", version=self.version)

        if self._commands:
            subs = parser.add_subparsers(dest="command")
            for cmd in self._commands.values():
                build_subparser(subs, cmd)

        return parser

    def parse_args(self, args: list[str] | None = None) -> argparse.Namespace:
        """Parse CLI arguments, exiting on missing subcommand."""
        parser = self.build_parser()
        ns = parser.parse_args(args)

        if not getattr(ns, "command", None):
            parser.print_help()
            sys.exit(1)

        return ns

    # -- Dispatch --

    async def dispatch(self, ns: argparse.Namespace) -> dict[str, Any]:
        """Dispatch parsed args to the matching command handler."""
        cmd_name: str = ns.command
        cmd = self._commands[cmd_name]

        # Build kwargs from namespace, matching handler param dests
        kwargs: dict[str, Any] = {}
        for p in cmd.params:
            kwargs[p.name] = getattr(ns, p.dest, p.default)

        handler = cmd.handler
        if inspect.iscoroutinefunction(handler):
            result = await handler(**kwargs)
        else:
            result = handler(**kwargs)

        return wrap_result(result)

    async def _run_async(self, args: list[str] | None = None) -> None:
        """Full async lifecycle: setup → dispatch → teardown → output."""
        ns = self.parse_args(args)

        for hook in self._setup_hooks:
            await hook()

        try:
            result = await self.dispatch(ns)
            ok = result.get("ok", True)
            print(json.dumps(result, indent=2, default=str))
            sys.exit(0 if ok else 1)
        finally:
            for hook in self._teardown_hooks:
                await hook()

    def run(self, args: list[str] | None = None) -> None:
        """Synchronous entry point: parse, run lifecycle, output JSON, exit."""
        try:
            asyncio.run(self._run_async(args))
        except SystemExit:
            raise
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as exc:
            err = format_error(exc)
            print(json.dumps(err, indent=2, default=str))
            sys.exit(1)

    # -- Internal --

    def _setup_sys_path(self) -> None:
        """Add the caller's ``src/`` directory to sys.path.

        Detects the calling script's location via ``inspect.stack()``
        and inserts ``<script_dir>/src`` at the front of ``sys.path``.
        """
        # The package source directory — skip frames originating from here
        _pkg_dir = os.path.dirname(os.path.abspath(__file__))

        for frame_info in inspect.stack():
            fpath = frame_info.filename
            if fpath == "<string>":
                continue
            abs_fpath = os.path.abspath(fpath)
            # Skip frames from within this package's own source
            if abs_fpath.startswith(_pkg_dir):
                continue
            script_dir = os.path.dirname(abs_fpath)
            src_dir = os.path.join(script_dir, "src")
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            break


def _first_line(text: str) -> str:
    """Return the first non-empty line of a docstring."""
    for line in text.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
