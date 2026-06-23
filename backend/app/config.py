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

    @property
    def has_env_defaults(self) -> bool:
        """True when the .env provides at least an endpoint to connect with."""
        return bool(self.endpoint)


def get_settings() -> Settings:
    """Return a freshly loaded :class:`Settings` instance.

    Loaded fresh (rather than cached) so edits to .env are picked up on restart
    and so tests can monkeypatch the environment.
    """
    return Settings()
