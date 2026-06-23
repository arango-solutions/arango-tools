"""Tool schema, command preview, and streaming execution endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.config import get_settings
from app.connection import store
from app.runner import ToolNotFoundError, resolve_binary, run_stream, terminate
from app.tools.builder import build_argv, validate_params
from app.tools.registry import ToolSpec, get_tool, list_tools

router = APIRouter(prefix="/api/tools", tags=["tools"])


class PreviewRequest(BaseModel):
    params: dict = {}


class PreviewResponse(BaseModel):
    argv: list[str]
    errors: list[str]
    connected: bool


@router.get("", response_model=list[ToolSpec])
async def get_tools() -> list[ToolSpec]:
    return list_tools()


@router.get("/{name}", response_model=ToolSpec)
async def get_tool_spec(name: str) -> ToolSpec:
    tool = get_tool(name)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool '{name}'.")
    return tool


@router.post("/{name}/preview", response_model=PreviewResponse)
async def preview(name: str, req: PreviewRequest) -> PreviewResponse:
    tool = get_tool(name)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool '{name}'.")

    connection = store.get()
    errors = validate_params(tool, req.params)
    if tool.connects and connection is None:
        errors.append("Not connected. Configure a connection first.")

    argv = build_argv(tool, req.params, connection, mask_password=True)
    return PreviewResponse(argv=argv, errors=errors, connected=connection is not None)


@router.websocket("/{name}/run")
async def run(websocket: WebSocket, name: str) -> None:
    await websocket.accept()
    tool = get_tool(name)
    if tool is None:
        await websocket.send_json({"type": "error", "data": f"Unknown tool '{name}'."})
        await websocket.close()
        return

    try:
        message = await websocket.receive_json()
    except WebSocketDisconnect:
        return
    params = message.get("params", {}) if isinstance(message, dict) else {}

    connection = store.get()
    errors = validate_params(tool, params)
    if tool.connects and connection is None:
        errors.append("Not connected. Configure a connection first.")
    if errors:
        await websocket.send_json({"type": "error", "data": "; ".join(errors)})
        await websocket.send_json({"type": "exit", "code": 1})
        await websocket.close()
        return

    settings = get_settings()
    try:
        binary = resolve_binary(tool.binary, settings.tools_bin)
    except ToolNotFoundError as exc:
        await websocket.send_json({"type": "error", "data": str(exc)})
        await websocket.send_json({"type": "exit", "code": 127})
        await websocket.close()
        return

    argv = build_argv(tool, params, connection, binary=binary)
    masked = build_argv(tool, params, connection, binary=binary, mask_password=True)
    await websocket.send_json({"type": "command", "data": masked})

    proc_holder: dict = {}

    def on_start(proc) -> None:
        proc_holder["proc"] = proc

    async def watch_for_cancel() -> None:
        try:
            while True:
                msg = await websocket.receive_json()
                if isinstance(msg, dict) and msg.get("action") == "cancel":
                    proc = proc_holder.get("proc")
                    if proc is not None:
                        await terminate(proc)
                    return
        except WebSocketDisconnect:
            proc = proc_holder.get("proc")
            if proc is not None:
                await terminate(proc)

    cancel_task = asyncio.create_task(watch_for_cancel())
    try:
        async for event in run_stream(argv, on_start=on_start):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        proc = proc_holder.get("proc")
        if proc is not None:
            await terminate(proc)
    finally:
        cancel_task.cancel()
        try:
            await websocket.close()
        except RuntimeError:
            pass
