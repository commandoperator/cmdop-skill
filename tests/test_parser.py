"""Tests for argparse generation from function signatures."""

from __future__ import annotations

import argparse

from cmdop_skill._arg import Arg
from cmdop_skill._parser import CommandInfo, build_subparser, extract_params
from cmdop_skill._types import MISSING


class TestExtractParams:
    def test_simple_str_param(self) -> None:
        async def send(to: str = Arg(help="Recipient", required=True)) -> dict:
            return {}

        params = extract_params(send)
        assert len(params) == 1
        p = params[0]
        assert p.name == "to"
        assert p.cli_name == "--to"
        assert p.required is True
        assert p.help == "Recipient"

    def test_underscore_to_hyphen(self) -> None:
        async def fetch(fetch_url: str = Arg(required=True)) -> dict:
            return {}

        params = extract_params(fetch)
        assert params[0].cli_name == "--fetch-url"
        assert params[0].dest == "fetch_url"

    def test_custom_cli_name(self) -> None:
        async def send(from_account: str = Arg("--from", default="")) -> dict:
            return {}

        params = extract_params(send)
        p = params[0]
        assert p.cli_name == "--from"
        # "from" is a keyword, so dest should be "from_"
        assert p.dest == "from_"

    def test_custom_dest(self) -> None:
        async def send(from_account: str = Arg("--from", dest="from_account", default="")) -> dict:
            return {}

        params = extract_params(send)
        assert params[0].dest == "from_account"

    def test_bool_becomes_store_true(self) -> None:
        async def run(verbose: bool = Arg()) -> dict:
            return {}

        params = extract_params(run)
        p = params[0]
        assert p.action == "store_true"
        assert p.default is False

    def test_int_type(self) -> None:
        async def fetch(limit: int = Arg(default=10)) -> dict:
            return {}

        params = extract_params(fetch)
        assert params[0].annotation is int
        assert params[0].default == 10

    def test_no_arg_with_default(self) -> None:
        async def run(mode: str = "fast") -> dict:
            return {}

        params = extract_params(run)
        p = params[0]
        assert p.default == "fast"
        assert p.required is False

    def test_no_arg_no_default(self) -> None:
        async def run(query: str) -> dict:
            return {}

        params = extract_params(run)
        p = params[0]
        assert p.required is True

    def test_choices(self) -> None:
        async def run(mode: str = Arg(choices=("fast", "slow"), default="fast")) -> dict:
            return {}

        params = extract_params(run)
        assert params[0].choices == ("fast", "slow")

    def test_multiple_params(self) -> None:
        async def send(
            to: str = Arg(required=True),
            subject: str = Arg(required=True),
            body: str = Arg(required=True),
        ) -> dict:
            return {}

        params = extract_params(send)
        assert len(params) == 3
        assert [p.name for p in params] == ["to", "subject", "body"]


class TestBuildSubparser:
    def test_builds_subparser(self) -> None:
        async def greet(name: str = Arg(help="Who", required=True)) -> dict:
            return {}

        cmd = CommandInfo(
            name="greet",
            handler=greet,
            help="Say hello",
            params=extract_params(greet),
        )

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        build_subparser(subs, cmd)

        ns = parser.parse_args(["greet", "--name", "World"])
        assert ns.command == "greet"
        assert ns.name == "World"

    def test_bool_flag(self) -> None:
        async def run(verbose: bool = Arg()) -> dict:
            return {}

        cmd = CommandInfo(
            name="run",
            handler=run,
            help="Run it",
            params=extract_params(run),
        )

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        build_subparser(subs, cmd)

        ns = parser.parse_args(["run", "--verbose"])
        assert ns.verbose is True

        ns2 = parser.parse_args(["run"])
        assert ns2.verbose is False

    def test_int_type_parsing(self) -> None:
        async def fetch(limit: int = Arg(default=10)) -> dict:
            return {}

        cmd = CommandInfo(
            name="fetch",
            handler=fetch,
            help="Fetch stuff",
            params=extract_params(fetch),
        )

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        build_subparser(subs, cmd)

        ns = parser.parse_args(["fetch", "--limit", "42"])
        assert ns.limit == 42
        assert isinstance(ns.limit, int)
