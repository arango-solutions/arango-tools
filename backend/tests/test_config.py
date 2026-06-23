"""Tests for environment-driven configuration (container-safe, env-only)."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings


def _clear_arango_env(monkeypatch) -> None:
    """Ensure no ARANGO_* vars or local .env leak into a test's expectations."""
    for key in (
        "ARANGO_ENDPOINT",
        "ARANGO_DATABASE",
        "ARANGO_USERNAME",
        "ARANGO_PASSWORD",
        "ARANGO_TOOLS_BIN",
        "ARANGO_STATIC_DIR",
        "ARANGO_CORS_ORIGINS",
        "ARANGO_ENV_FILE",
    ):
        monkeypatch.delenv(key, raising=False)
    # Point env-file discovery at a temp dir so a developer's real .env (if any)
    # does not influence the test.
    monkeypatch.setenv("ARANGO_ENV_FILE", str(Path("/nonexistent/.env")))


def test_settings_load_from_env_without_dotenv(monkeypatch):
    _clear_arango_env(monkeypatch)
    monkeypatch.setenv("ARANGO_ENDPOINT", "http://db:8529")
    monkeypatch.setenv("ARANGO_DATABASE", "mydb")
    monkeypatch.setenv("ARANGO_STATIC_DIR", "/srv/static")

    settings = get_settings()
    assert settings.endpoint == "http://db:8529"
    assert settings.database == "mydb"
    assert settings.static_dir == "/srv/static"
    assert settings.has_env_defaults is True


def test_defaults_when_unset(monkeypatch):
    _clear_arango_env(monkeypatch)
    settings = get_settings()
    assert settings.endpoint is None
    assert settings.static_dir is None
    assert settings.has_env_defaults is False
    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_cors_origin_list_parsing(monkeypatch):
    _clear_arango_env(monkeypatch)
    monkeypatch.setenv(
        "ARANGO_CORS_ORIGINS",
        "https://app.example.com/, http://localhost:3000 ,https://app.example.com",
    )
    settings = get_settings()
    # Trimmed, trailing slash stripped, de-duplicated, order preserved.
    assert settings.cors_origin_list == [
        "https://app.example.com",
        "http://localhost:3000",
    ]
