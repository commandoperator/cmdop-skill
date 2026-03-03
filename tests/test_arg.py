"""Tests for the Arg descriptor."""

from __future__ import annotations

from cmdop_skill._arg import Arg
from cmdop_skill._types import MISSING


class TestArg:
    def test_default_values(self) -> None:
        a = Arg()
        assert a.cli_name is None
        assert a.help == ""
        assert a.required is False
        assert a.choices is None
        assert a.action is None
        assert a.dest is None
        assert a.nargs is None

    def test_has_default_missing(self) -> None:
        a = Arg()
        assert a.has_default() is False

    def test_has_default_explicit(self) -> None:
        a = Arg(default="")
        assert a.has_default() is True

    def test_has_default_none(self) -> None:
        a = Arg(default=None)
        assert a.has_default() is True

    def test_cli_name_override(self) -> None:
        a = Arg("--from", dest="from_account")
        assert a.cli_name == "--from"
        assert a.dest == "from_account"

    def test_choices(self) -> None:
        a = Arg(choices=("low", "medium", "high"))
        assert a.choices == ("low", "medium", "high")

    def test_action(self) -> None:
        a = Arg(action="store_true", default=False)
        assert a.action == "store_true"
        assert a.default is False

    def test_positional_cli_name(self) -> None:
        a = Arg("--my-flag", help="A flag", required=True)
        assert a.cli_name == "--my-flag"
        assert a.help == "A flag"
        assert a.required is True
