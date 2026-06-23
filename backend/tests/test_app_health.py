"""Tests for the liveness (/api/health) and readiness (/api/ready) endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

import app.main as main_mod


def test_health_is_always_ok():
    with TestClient(main_mod.app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_ok_when_binary_resolves(monkeypatch):
    monkeypatch.setattr(
        main_mod, "resolve_binary", lambda binary, tools_bin=None: "/usr/bin/arangosh"
    )
    with TestClient(main_mod.app) as client:
        resp = client.get("/api/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_ready_503_when_binary_missing(monkeypatch):
    def boom(binary, tools_bin=None):
        raise main_mod.ToolNotFoundError("missing tools")

    monkeypatch.setattr(main_mod, "resolve_binary", boom)
    with TestClient(main_mod.app) as client:
        resp = client.get("/api/ready")
    assert resp.status_code == 503
    assert "missing tools" in resp.json()["detail"]
