"""Tests for JSON output helpers."""

from __future__ import annotations

import pytest

from cmdop_skill._output import format_error, wrap_result


class TestWrapResult:
    def test_passthrough_with_ok(self) -> None:
        result = {"ok": True, "data": [1, 2, 3]}
        assert wrap_result(result) == {"ok": True, "data": [1, 2, 3]}

    def test_passthrough_with_ok_false(self) -> None:
        result = {"ok": False, "error": "bad"}
        assert wrap_result(result) == {"ok": False, "error": "bad"}

    def test_wraps_without_ok(self) -> None:
        result = {"message": "hello"}
        assert wrap_result(result) == {"ok": True, "message": "hello"}

    def test_wraps_empty_dict(self) -> None:
        assert wrap_result({}) == {"ok": True}


class TestFormatError:
    def test_basic_error(self) -> None:
        exc = ValueError("something broke")
        result = format_error(exc)
        assert result["ok"] is False
        assert result["error"] == "something broke"
        assert result["code"] == "SKILL_ERROR"
        assert "traceback" in result

    def test_custom_code(self) -> None:
        exc = RuntimeError("auth failed")
        result = format_error(exc, code="AUTH_ERROR")
        assert result["code"] == "AUTH_ERROR"

    def test_traceback_is_list(self) -> None:
        try:
            raise TypeError("oops")
        except TypeError as e:
            result = format_error(e)
        assert isinstance(result["traceback"], list)
        assert len(result["traceback"]) > 0
