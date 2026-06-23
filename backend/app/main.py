"""FastAPI application entry point for the Arango Tools GUI backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import connection, tools

app = FastAPI(
    title="Arango Tools GUI",
    description="Wraps the ArangoDB client tools and streams their output to a web UI.",
    version="0.1.0",
)

# The Vite dev server proxies API/WS calls, but allow direct cross-origin access
# during development too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router)
app.include_router(tools.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
