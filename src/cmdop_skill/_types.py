"""Type aliases for cmdop_skill."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Union

# Command handler: sync or async function returning a dict
Handler = Union[Callable[..., dict[str, Any]], Callable[..., Awaitable[dict[str, Any]]]]

# Lifecycle hook: async no-arg function
LifecycleHook = Callable[[], Awaitable[None]]


class _MissingSentinel:
    """Sentinel for distinguishing 'not provided' from None."""

    _instance: _MissingSentinel | None = None

    def __new__(cls) -> _MissingSentinel:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<MISSING>"

    def __bool__(self) -> bool:
        return False


MISSING = _MissingSentinel()
