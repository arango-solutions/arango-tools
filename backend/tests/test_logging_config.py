"""Tests for structured JSON logging."""

from __future__ import annotations

import json
import logging

from app.logging_config import JsonFormatter


def _record(**kwargs) -> logging.LogRecord:
    defaults = dict(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    defaults.update(kwargs)
    return logging.LogRecord(**defaults)


def test_json_formatter_emits_valid_json_with_expected_fields():
    formatted = JsonFormatter().format(_record())
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["message"] == "hello world"
    assert "timestamp" in parsed


def test_json_formatter_includes_exception_info():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        formatted = JsonFormatter().format(
            _record(level=logging.ERROR, exc_info=sys.exc_info())
        )
    parsed = json.loads(formatted)
    assert "exc_info" in parsed
    assert "ValueError" in parsed["exc_info"]
