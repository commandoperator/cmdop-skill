"""Arg descriptor — bridges function parameters to argparse arguments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from cmdop_skill._types import MISSING, _MissingSentinel


@dataclass
class Arg:
    """Descriptor that captures argparse configuration in a function signature.

    Usage::

        @skill.command
        async def send(
            to: str = Arg(help="Recipient(s)", required=True),
            subject: str = Arg(required=True),
            body: str = Arg(required=True),
            from_account: str = Arg("--from", help="Sender account", default=""),
        ) -> dict:
            ...
    """

    cli_name: str | None = None
    help: str = ""
    required: bool = False
    default: Any = MISSING
    choices: Sequence[str] | None = None
    action: str | None = None
    dest: str | None = None
    nargs: str | None = None

    def __init__(
        self,
        cli_name: str | None = None,
        *,
        help: str = "",
        required: bool = False,
        default: Any = MISSING,
        choices: Sequence[str] | None = None,
        action: str | None = None,
        dest: str | None = None,
        nargs: str | None = None,
    ) -> None:
        self.cli_name = cli_name
        self.help = help
        self.required = required
        self.default = default
        self.choices = choices
        self.action = action
        self.dest = dest
        self.nargs = nargs

    def has_default(self) -> bool:
        """Return True if a default value was explicitly provided."""
        return not isinstance(self.default, _MissingSentinel)
