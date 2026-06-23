# Arango Tools GUI

A web GUI for the Arango client tools. The backend shells out to the installed
`arango*` binaries and streams their output to the browser; the frontend presents
each tool as its own tab and lets you connect to an instance via a `.env` file or
by entering credentials manually.

## Tools

Each of the Arango 4.0 core client tools gets its own tab:

| Tab | Binary | Purpose |
| --- | --- | --- |
| Dump | `arangodump` | Back up databases/collections to a directory |
| Restore | `arangorestore` | Load a dump back into an instance |
| Backup | `arangobackup` | Hot backup operations (create/list/restore/…) |
| Import | `arangoimport` | Bulk-import JSON/JSONL/CSV/TSV |
| Export | `arangoexport` | Bulk-export collections or AQL results (JSON/CSV/XML) |
| Bench | `arangobench` | Performance/functional benchmarks |
| Inspect | `arangoinspect` | Gather server setup info for troubleshooting |
| Shell | `arangosh` | Run JavaScript non-interactively |
| VPack | `arangovpack` | Convert/validate VelocyPack and JSON (local files) |
| Starter | `arangodb` | Deploy/manage instances (ArangoDB Starter) |

> Foxx CLI is intentionally excluded: Foxx and `foxx-cli` were removed in Arango 4.0.

## Architecture

- **Backend**: Python, FastAPI, managed with [uv]. A declarative tool registry
  drives both the JSON schema sent to the UI and argv construction; a subprocess
  runner streams stdout/stderr over a WebSocket.
- **Frontend**: TypeScript, React, Tailwind, built with Vite. A schema-driven
  form renders each tool, with a live command preview and a streaming console.

```
arango-tools/
├── backend/    # FastAPI app (app/), tests, pyproject.toml (uv)
├── frontend/   # Vite + React + TS + Tailwind
├── .env.example
└── README.md
```

## Prerequisites

- The ArangoDB client tools on your `PATH` (or set `ARANGO_TOOLS_BIN`).
- [uv](https://docs.astral.sh/uv/) for the backend.
- Node.js 18+ / npm for the frontend.

## How tool execution works (read this before running)

This app is a **GUI wrapper around the real ArangoDB command-line programs** — it
does not reimplement what `arangodump`, `arangoimport`, etc. do. When you click
**Run** in the UI, the backend spawns the actual `arango*` executable as a child
process and streams its stdout/stderr back to the browser over a WebSocket.

Because of this, the binaries must physically exist on the **machine running the
FastAPI backend** (not your browser's machine):

1. **Install the ArangoDB client tools** on the backend host. They ship with a
   full ArangoDB installation, or you can install the client-only package. See the
   [ArangoDB tools docs](https://docs.arango.ai/arangodb/stable/components/tools/).
2. **Make them discoverable** by either:
   - ensuring they are on `PATH` (verify with `which arangodump`), or
   - setting `ARANGO_TOOLS_BIN=/path/to/arangodb/bin` in your `.env`.

The backend resolves each binary in `backend/app/runner.py` (`resolve_binary`):
it prefers `ARANGO_TOOLS_BIN`, then falls back to `PATH`. If a binary cannot be
found, the run fails gracefully with an error event and exit code `127`
("command not found") instead of crashing.

Implications:

- **Host-dependent:** the installed tools must match the OS/architecture of the
  backend host.
- **Filesystem is the backend's, not yours:** path-based options (e.g. dump
  output directory, import source file) and the file-only tools `arangovpack`
  (VPack) and `arangodb` (Starter) operate on the **backend** host's filesystem.
- **Reproducible deployments:** a common approach is to run the backend in a
  Docker image that bundles the ArangoDB client tools so the binaries are always
  present and version-matched. (A `docker-compose.yml` is a planned follow-up and
  not part of the initial scope.)

> The same guidance is available in the app itself under the **How To** tab.

## Setup

1. (Optional) Configure default connection settings:

   ```bash
   cp .env.example .env
   # edit .env
   ```

2. Backend:

   ```bash
   cd backend
   uv sync
   uv run uvicorn app.main:app --reload --port 8000
   ```

3. Frontend (in another terminal):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Open http://localhost:5173. The Vite dev server proxies `/api` (REST + WebSocket)
   to the backend on port 8000.

## Connecting

In the **Connection** panel, either select **Use .env** (if the backend found
defaults) or choose **Manual** and enter the endpoint/URI, database, username, and
password. Use **Test connection** to validate; tool tabs that require a server are
enabled once connected. `http(s)://` endpoints are converted to the tools'
`tcp://`/`ssl://` form automatically.

## Testing

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm test
```

## Security notes

- Commands are built as argument lists and spawned without a shell (no shell
  injection); only registry-defined binaries can be executed.
- Passwords are masked in command previews and are never logged. Because the tools
  accept credentials as CLI flags, run the backend in a trusted environment.
