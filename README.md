# Arango Tools GUI

A web GUI for the ArangoDB client tools. The backend shells out to the installed
`arango*` binaries and streams their output to the browser; the frontend presents
each tool as its own tab and lets you connect to an instance via a `.env` file or
by entering credentials manually.

## Tools

Each of the ArangoDB 4.0 core client tools gets its own tab:

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

> Foxx CLI is intentionally excluded: Foxx and `foxx-cli` were removed in ArangoDB 4.0.

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
