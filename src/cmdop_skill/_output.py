"""JSON output helpers for CMDOP skills."""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any


def json_output(ok: bool, **kwargs: Any) -> None:
    """Print JSON result to stdout and exit.

    This is the standard CMDOP skill output function.
    """
    result: dict[str, Any] = {"ok": ok, **kwargs}
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if ok else 1)


def wrap_result(result: dict[str, Any]) -> dict[str, Any]:
    """Wrap a handler return value into standard CMDOP format.

    If the dict already has an ``ok`` key, pass through as-is.
    Otherwise wrap with ``{"ok": True, ...}``.
    """
    if "ok" in result:
        return result
    return {"ok": True, **result}


def format_error(exc: BaseException, code: str = "SKILL_ERROR") -> dict[str, Any]:
    """Format an exception into a CMDOP error result."""
    return {
        "ok": False,
        "error": str(exc),
        "code": code,
        "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__),
    }
