"""FastAPI application entry point for the Arango Tools GUI backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import connection, tools
from app.runner import ToolNotFoundError, resolve_binary

# A representative client tool used to verify the bundled binaries are present.
_READINESS_PROBE_BINARY = "arangosh"

app = FastAPI(
    title="Arango Tools GUI",
    description="Wraps the ArangoDB client tools and streams their output to a web UI.",
    version="0.1.0",
)

_settings = get_settings()

# CORS is only meaningful when the UI is served from a different origin (e.g. the
# Vite dev server). When the static bundle is served by this app (the container /
# BYOC path) the UI is same-origin and these origins are unused.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router)
app.include_router(tools.router)


@app.get("/api/health")
async def health() -> dict:
    """Liveness: the process is up and serving. Cheap and always-on."""
    return {"status": "ok"}


@app.get("/api/ready")
async def ready() -> dict:
    """Readiness: the client tools are actually resolvable on this host.

    Returns 503 until the bundled binaries can be found so orchestrators don't
    route traffic to an instance that can't run any tool.
    """
    settings = get_settings()
    try:
        resolve_binary(_READINESS_PROBE_BINARY, settings.tools_bin)
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ready"}


def _mount_frontend(application: FastAPI, static_dir: str | None) -> None:
    """Serve the built frontend (single-origin) when ``static_dir`` is configured.

    Static assets are served from ``<static_dir>/assets``; any other non-API GET
    falls back to ``index.html`` so client-side routing keeps working. When
    ``static_dir`` is unset (local dev), the API runs alone and Vite serves the UI.
    """
    if not static_dir:
        return
    root = Path(static_dir).resolve()
    if not root.is_dir():
        return
    index_file = root / "index.html"

    assets_dir = root / "assets"
    if assets_dir.is_dir():
        application.mount(
            "/assets", StaticFiles(directory=assets_dir), name="assets"
        )

    @application.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str) -> FileResponse:
        # Never let the catch-all shadow the API surface.
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (root / full_path).resolve()
        if (
            full_path
            and candidate.is_file()
            and candidate.is_relative_to(root)
        ):
            return FileResponse(candidate)
        return FileResponse(index_file)


_mount_frontend(app, _settings.static_dir)
