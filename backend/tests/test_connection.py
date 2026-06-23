"""Tests for endpoint normalization, masking, and connection testing."""

from __future__ import annotations

import httpx
import pytest

from app import connection as conn_mod
from app.connection import (
    ConnectionState,
    to_http_endpoint,
    to_tools_endpoint,
)

run_connection_test = conn_mod.test_connection


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("http://localhost:8529", "http://localhost:8529"),
        ("https://localhost:8529", "https://localhost:8529"),
        ("tcp://localhost:8529", "http://localhost:8529"),
        ("ssl://localhost:8529", "https://localhost:8529"),
        ("localhost:8529", "http://localhost:8529"),
        ("http://localhost:8529/", "http://localhost:8529"),
    ],
)
def test_to_http_endpoint(raw, expected):
    assert to_http_endpoint(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("http://localhost:8529", "tcp://localhost:8529"),
        ("https://localhost:8529", "ssl://localhost:8529"),
        ("tcp://localhost:8529", "tcp://localhost:8529"),
        ("localhost:8529", "tcp://localhost:8529"),
    ],
)
def test_to_tools_endpoint(raw, expected):
    assert to_tools_endpoint(raw) == expected


def test_masked_hides_password():
    state = ConnectionState(endpoint="http://x:8529", password="secret", source="manual")
    masked = state.masked()
    assert masked["password"] == "********"
    assert masked["has_password"] is True


def test_masked_empty_password():
    state = ConnectionState(endpoint="http://x:8529", password="", source="manual")
    masked = state.masked()
    assert masked["password"] == ""
    assert masked["has_password"] is False


async def test_connection_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/_db/_system/_api/version"
        return httpx.Response(200, json={"version": "4.0.0", "server": "arango"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs.pop("verify", None)
        return real_client(transport=transport)

    monkeypatch.setattr(conn_mod.httpx, "AsyncClient", client_factory)

    state = ConnectionState(endpoint="http://x:8529", source="manual")
    result = await run_connection_test(state)
    assert result.ok is True
    assert result.version == "4.0.0"


async def test_connection_auth_failure(monkeypatch):
    transport = httpx.MockTransport(lambda req: httpx.Response(401, json={}))
    real_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs.pop("verify", None)
        return real_client(transport=transport)

    monkeypatch.setattr(conn_mod.httpx, "AsyncClient", client_factory)

    state = ConnectionState(endpoint="http://x:8529", source="manual")
    result = await run_connection_test(state)
    assert result.ok is False
    assert "401" in result.message
