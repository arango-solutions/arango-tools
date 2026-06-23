"""Async subprocess execution with line-buffered output streaming."""

from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any


class ToolNotFoundError(RuntimeError):
    """Raised when a tool binary cannot be located."""


def resolve_binary(binary: str, tools_bin: str | None = None) -> str:
    """Locate a tool binary, preferring ``tools_bin`` then the PATH."""
    if tools_bin:
        candidate = Path(tools_bin) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
        # Allow Windows-style names too.
        candidate_exe = candidate.with_suffix(".exe")
        if candidate_exe.exists():
            return str(candidate_exe)
    found = shutil.which(binary)
    if found:
        return found
    raise ToolNotFoundError(
        f"Could not find '{binary}'. Install the ArangoDB client tools and ensure "
        f"they are on PATH, or set ARANGO_TOOLS_BIN."
    )


async def run_stream(
    argv: list[str],
    *,
    cwd: str | None = None,
    on_start: Callable[[asyncio.subprocess.Process], Any] | None = None,
) -> AsyncIterator[dict]:
    """Spawn ``argv`` and yield event dicts.

    Events: ``{"type": "stdout"|"stderr", "data": line}`` per line and a final
    ``{"type": "exit", "code": int}``. ``on_start`` receives the process so the
    caller can cancel it.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        yield {"type": "stderr", "data": f"Failed to start process: {exc}"}
        yield {"type": "exit", "code": 127}
        return

    if on_start is not None:
        on_start(proc)

    queue: asyncio.Queue[tuple[str, str] | None] = asyncio.Queue()

    async def pump(stream: asyncio.StreamReader, kind: str) -> None:
        while True:
            line = await stream.readline()
            if not line:
                break
            await queue.put((kind, line.decode(errors="replace").rstrip("\r\n")))
        await queue.put(None)  # sentinel: this stream is done

    assert proc.stdout is not None and proc.stderr is not None
    pumps = [
        asyncio.create_task(pump(proc.stdout, "stdout")),
        asyncio.create_task(pump(proc.stderr, "stderr")),
    ]

    finished_streams = 0
    while finished_streams < len(pumps):
        item = await queue.get()
        if item is None:
            finished_streams += 1
            continue
        kind, data = item
        yield {"type": kind, "data": data}

    await asyncio.gather(*pumps, return_exceptions=True)
    code = await proc.wait()
    yield {"type": "exit", "code": code}


async def terminate(proc: asyncio.subprocess.Process, grace: float = 3.0) -> None:
    """Terminate a process, escalating to kill after ``grace`` seconds."""
    if proc.returncode is not None:
        return
    try:
        proc.terminate()
    except ProcessLookupError:
        return
    try:
        await asyncio.wait_for(proc.wait(), timeout=grace)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
