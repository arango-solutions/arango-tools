"""Tests for graceful termination of tracked tool subprocesses."""

from __future__ import annotations

import asyncio

from app import runner


async def test_terminate_all_kills_registered_processes():
    proc = await asyncio.create_subprocess_exec(
        "sleep",
        "30",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    runner.register_process(proc)
    assert proc.returncode is None

    await runner.terminate_all(grace=2.0)

    assert proc.returncode is not None
    assert proc not in runner._active_processes


async def test_terminate_all_is_safe_with_no_processes():
    # Should not raise when the registry is empty.
    await runner.terminate_all()
