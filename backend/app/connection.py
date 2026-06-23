"""Connection state management and validation against an ArangoDB instance."""

from __future__ import annotations

from typing import Literal

import httpx
from pydantic import BaseModel, Field

ConnectionSource = Literal["env", "manual"]


class ConnectionState(BaseModel):
    """A resolved set of connection parameters."""

    endpoint: str = Field(..., description="ArangoDB endpoint, e.g. http://localhost:8529")
    database: str = Field(default="_system")
    username: str = Field(default="root")
    password: str = Field(default="")
    source: ConnectionSource = "manual"

    def masked(self) -> dict:
        """Serialize without exposing the password."""
        data = self.model_dump()
        data["password"] = "********" if self.password else ""
        data["has_password"] = bool(self.password)
        return data


class ConnectionTestResult(BaseModel):
    ok: bool
    message: str
    version: str | None = None
    server: str | None = None


def normalize_endpoint(endpoint: str) -> str:
    """Strip whitespace and trailing slashes from an endpoint string."""
    return endpoint.strip().rstrip("/")


def to_http_endpoint(endpoint: str) -> str:
    """Return an http(s):// endpoint suitable for the ArangoDB HTTP API.

    The arango client tools use ``tcp://`` and ``ssl://`` schemes; convert those
    to ``http://`` / ``https://`` for use with httpx.
    """
    ep = normalize_endpoint(endpoint)
    if ep.startswith("tcp://"):
        return "http://" + ep[len("tcp://") :]
    if ep.startswith("ssl://"):
        return "https://" + ep[len("ssl://") :]
    if ep.startswith(("http://", "https://")):
        return ep
    # Bare host:port -> assume plain http.
    return "http://" + ep


def to_tools_endpoint(endpoint: str) -> str:
    """Return a ``tcp://`` / ``ssl://`` endpoint as expected by the arango tools."""
    ep = normalize_endpoint(endpoint)
    if ep.startswith("http://"):
        return "tcp://" + ep[len("http://") :]
    if ep.startswith("https://"):
        return "ssl://" + ep[len("https://") :]
    if ep.startswith(("tcp://", "ssl://")):
        return ep
    return "tcp://" + ep


async def test_connection(state: ConnectionState, timeout: float = 5.0) -> ConnectionTestResult:
    """Validate a connection by calling ``GET /_api/version`` on the instance."""
    base = to_http_endpoint(state.endpoint)
    db = state.database or "_system"
    url = f"{base}/_db/{db}/_api/version"
    auth = (state.username, state.password)
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            resp = await client.get(url, auth=auth, params={"details": "false"})
    except httpx.HTTPError as exc:
        return ConnectionTestResult(ok=False, message=f"Connection failed: {exc}")

    if resp.status_code == 401:
        return ConnectionTestResult(ok=False, message="Authentication failed (401). Check credentials.")
    if resp.status_code >= 400:
        return ConnectionTestResult(
            ok=False, message=f"Server returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    try:
        data = resp.json()
    except ValueError:
        return ConnectionTestResult(ok=False, message="Unexpected non-JSON response from server.")
    return ConnectionTestResult(
        ok=True,
        message="Connected successfully.",
        version=data.get("version"),
        server=data.get("server"),
    )


class ConnectionStore:
    """In-memory holder for the active connection (single-session backend)."""

    def __init__(self) -> None:
        self._state: ConnectionState | None = None

    def get(self) -> ConnectionState | None:
        return self._state

    def set(self, state: ConnectionState) -> None:
        self._state = state

    def clear(self) -> None:
        self._state = None


# Module-level singleton used by the routers.
store = ConnectionStore()
