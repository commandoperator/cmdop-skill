"""Auto-generate argparse subcommands from function signatures."""

from __future__ import annotations

import argparse
import inspect
from dataclasses import dataclass
from typing import Any, Sequence

from cmdop_skill._arg import Arg
from cmdop_skill._types import MISSING, Handler, _MissingSentinel


# Type mapping: Python type annotation → argparse type
_TYPE_MAP: dict[type, type] = {
    str: str,
    int: int,
    float: float,
}


@dataclass
class ParamInfo:
    """Extracted parameter info ready for argparse."""

    name: str
    cli_name: str
    dest: str
    annotation: type
    help: str
    required: bool
    default: Any
    choices: Sequence[str] | None
    action: str | None
    nargs: str | None


@dataclass
class CommandInfo:
    """A registered command with its handler and metadata."""

    name: str
    handler: Handler
    help: str
    params: list[ParamInfo]


def extract_params(func: Handler) -> list[ParamInfo]:
    """Extract parameter info from a function's signature and type hints."""
    sig = inspect.signature(func)
    hints = _get_type_hints_safe(func)
    params: list[ParamInfo] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        annotation = hints.get(param_name, str)
        if annotation is inspect.Parameter.empty:
            annotation = str

        default = param.default
        arg: Arg | None = None

        if isinstance(default, Arg):
            arg = default
            default = arg.default if arg.has_default() else MISSING
        elif default is inspect.Parameter.empty:
            default = MISSING

        # Determine CLI flag name
        if arg is not None and arg.cli_name:
            cli_name = arg.cli_name
        else:
            cli_name = f"--{param_name.replace('_', '-')}"

        # Determine dest (argparse destination attribute name)
        if arg is not None and arg.dest:
            dest = arg.dest
        else:
            # --from-account → from_account, --from → from_
            raw_dest = cli_name.lstrip("-").replace("-", "_")
            # Avoid Python keyword collisions
            import keyword
            dest = f"{raw_dest}_" if keyword.iskeyword(raw_dest) else raw_dest

        # Determine required
        if arg is not None and arg.required:
            required = True
        elif isinstance(default, _MissingSentinel):
            required = True
        else:
            required = False

        # Bool type → store_true action
        action = arg.action if arg is not None else None
        nargs = arg.nargs if arg is not None else None
        if annotation is bool and action is None:
            action = "store_true"
            if isinstance(default, _MissingSentinel):
                default = False

        params.append(
            ParamInfo(
                name=param_name,
                cli_name=cli_name,
                dest=dest,
                annotation=annotation,
                help=arg.help if arg is not None else "",
                required=required,
                default=default,
                choices=arg.choices if arg is not None else None,
                action=action,
                nargs=nargs,
            )
        )

    return params


def build_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    cmd: CommandInfo,
) -> argparse.ArgumentParser:
    """Add a subcommand to the argparse subparsers from a CommandInfo."""
    parser = subparsers.add_parser(cmd.name, help=cmd.help)

    for p in cmd.params:
        kwargs: dict[str, Any] = {}

        if p.help:
            kwargs["help"] = p.help

        if p.action:
            kwargs["action"] = p.action
            if not isinstance(p.default, _MissingSentinel):
                kwargs["default"] = p.default
        else:
            if p.annotation in _TYPE_MAP:
                kwargs["type"] = _TYPE_MAP[p.annotation]

            if p.choices is not None:
                kwargs["choices"] = p.choices

            if p.nargs is not None:
                kwargs["nargs"] = p.nargs

            if p.required:
                kwargs["required"] = True

            if not isinstance(p.default, _MissingSentinel):
                kwargs["default"] = p.default

        # Set dest if it differs from what argparse would infer
        if p.dest != p.cli_name.lstrip("-").replace("-", "_"):
            kwargs["dest"] = p.dest

        parser.add_argument(p.cli_name, **kwargs)

    return parser


# Mapping from annotation string names to Python builtins (for `from __future__ import annotations`)
_BUILTIN_TYPE_NAMES: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "bytes": bytes,
}


def _get_type_hints_safe(func: Handler) -> dict[str, Any]:
    """Get type hints, resolving string annotations to actual types."""
    try:
        hints = inspect.get_annotations(func, eval_str=False)
    except Exception:
        return {}

    resolved: dict[str, Any] = {}
    for name, hint in hints.items():
        if isinstance(hint, str):
            # Resolve builtin type names from string annotations
            resolved[name] = _BUILTIN_TYPE_NAMES.get(hint, hint)
        else:
            resolved[name] = hint
    return resolved
