"""Tests for single-origin static frontend serving and SPA fallback."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def static_client(tmp_path, monkeypatch):
    """Build a fake frontend bundle, point the app at it, and yield a client.

    The app reads ``ARANGO_STATIC_DIR`` at import time, so we set the env var and
    reload ``app.main`` to exercise the mounted-static configuration. The module
    is reloaded again on teardown to restore the API-only default for other tests.
    """
    (tmp_path / "index.html").write_text("<!doctype html><title>spa</title>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('hi');")

    monkeypatch.setenv("ARANGO_STATIC_DIR", str(tmp_path))
    import app.main as main_mod

    main_mod = importlib.reload(main_mod)
    try:
        with TestClient(main_mod.app) as client:
            yield client
    finally:
        monkeypatch.delenv("ARANGO_STATIC_DIR", raising=False)
        importlib.reload(main_mod)


def test_health_still_works_with_static(static_client):
    resp = static_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root_serves_index_html(static_client):
    resp = static_client.get("/")
    assert resp.status_code == 200
    assert "spa" in resp.text


def test_assets_are_served(static_client):
    resp = static_client.get("/assets/app.js")
    assert resp.status_code == 200
    assert "console.log" in resp.text


def test_unknown_route_falls_back_to_spa(static_client):
    resp = static_client.get("/some/client/route")
    assert resp.status_code == 200
    assert "spa" in resp.text


def test_unknown_api_route_is_not_shadowed_by_spa(static_client):
    resp = static_client.get("/api/does-not-exist")
    assert resp.status_code == 404
