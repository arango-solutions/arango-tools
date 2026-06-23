# Arango Tools GUI - Backend

FastAPI service that wraps the ArangoDB client tools (`arangodump`, `arangorestore`,
`arangoimport`, etc.) by spawning the installed binaries and streaming their output
to the frontend over WebSockets.

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)
- The ArangoDB client tools available on `PATH` (or set `ARANGO_TOOLS_BIN`).

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

## Test

```bash
uv run pytest
```

## Configuration

Copy `../.env.example` to `../.env` (repo root) to provide default connection
settings. All values are optional; connection details can also be entered in the GUI.
