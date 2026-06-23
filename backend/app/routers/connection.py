"""Connection configuration and validation endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.connection import (
    ConnectionState,
    ConnectionTestResult,
    normalize_endpoint,
    store,
    test_connection,
)

router = APIRouter(prefix="/api/connection", tags=["connection"])


class ConnectionRequest(BaseModel):
    source: str = "manual"  # "manual" or "env"
    endpoint: str | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None


class ConnectionStatus(BaseModel):
    connected: bool
    env_available: bool
    env_defaults: dict | None = None
    current: dict | None = None


class ConnectionResponse(BaseModel):
    test: ConnectionTestResult
    current: dict | None = None


def _env_defaults() -> dict | None:
    settings = get_settings()
    if not settings.has_env_defaults:
        return None
    return {
        "endpoint": settings.endpoint,
        "database": settings.database or "_system",
        "username": settings.username or "root",
        "has_password": bool(settings.password),
    }


def _resolve_state(req: ConnectionRequest) -> ConnectionState:
    if req.source == "env":
        settings = get_settings()
        return ConnectionState(
            endpoint=normalize_endpoint(settings.endpoint or ""),
            database=settings.database or "_system",
            username=settings.username or "root",
            password=settings.password or "",
            source="env",
        )
    return ConnectionState(
        endpoint=normalize_endpoint(req.endpoint or ""),
        database=req.database or "_system",
        username=req.username or "root",
        password=req.password or "",
        source="manual",
    )


@router.get("", response_model=ConnectionStatus)
async def get_connection() -> ConnectionStatus:
    current = store.get()
    return ConnectionStatus(
        connected=current is not None,
        env_available=get_settings().has_env_defaults,
        env_defaults=_env_defaults(),
        current=current.masked() if current else None,
    )


@router.post("/test", response_model=ConnectionTestResult)
async def test(req: ConnectionRequest) -> ConnectionTestResult:
    state = _resolve_state(req)
    if not state.endpoint:
        return ConnectionTestResult(ok=False, message="An endpoint is required.")
    return await test_connection(state)


@router.post("", response_model=ConnectionResponse)
async def set_connection(req: ConnectionRequest) -> ConnectionResponse:
    state = _resolve_state(req)
    if not state.endpoint:
        return ConnectionResponse(
            test=ConnectionTestResult(ok=False, message="An endpoint is required."),
            current=None,
        )
    result = await test_connection(state)
    if result.ok:
        store.set(state)
    return ConnectionResponse(test=result, current=state.masked() if result.ok else None)


@router.delete("", response_model=ConnectionStatus)
async def clear_connection() -> ConnectionStatus:
    store.clear()
    return ConnectionStatus(
        connected=False,
        env_available=get_settings().has_env_defaults,
        env_defaults=_env_defaults(),
        current=None,
    )
