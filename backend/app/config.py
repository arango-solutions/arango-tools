"""Application configuration sourced from the environment / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The .env file lives at the repository root (one level above ``backend/``).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Connection and runtime defaults for the backend.

    All ArangoDB connection values are optional: when absent, the user supplies
    them through the GUI instead.
    """

    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", Path(".env")),
        env_prefix="ARANGO_",
        extra="ignore",
        case_sensitive=False,
    )

    endpoint: str | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    # Directory holding the arango* binaries. ``None`` => rely on PATH.
    tools_bin: str | None = None
    # Directory of the built frontend (``dist``). ``None`` => API only, which is
    # the default for local dev where Vite serves the UI. In the container this
    # points at the bundled static assets so the API and UI share one origin.
    static_dir: str | None = None
    # Comma-separated list of allowed CORS origins. Only relevant when the UI is
    # served from a different origin (e.g. the Vite dev server); when the static
    # bundle is served by this app the UI is same-origin and CORS is unused.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def has_env_defaults(self) -> bool:
        """True when the .env provides at least an endpoint to connect with."""
        return bool(self.endpoint)

    @property
    def cors_origin_list(self) -> list[str]:
        """Parsed, de-duplicated list of allowed CORS origins."""
        seen: list[str] = []
        for origin in self.cors_origins.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
        return seen


def get_settings() -> Settings:
    """Return a freshly loaded :class:`Settings` instance.

    Loaded fresh (rather than cached) so edits to .env are picked up on restart
    and so tests can monkeypatch the environment.
    """
    return Settings()
