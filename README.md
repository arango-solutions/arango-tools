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
- **Reproducible deployments:** the repo ships a `Dockerfile` that bundles the
  ArangoDB client tools so the binaries are always present and version-matched,
  and serves the UI + API from a single origin. See **Deployment (BYOC)** below.

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

## Deployment (BYOC)

The app ships as a single container that bundles the ArangoDB client tools and
serves the UI + API from one port (`8000`). It's designed to run in your own
cloud ("bring your own cloud").

### Build & run the image

```bash
# Build (pin the client tools to your supported ArangoDB line via ARANGODB_REPO)
docker build -t arango-tools:latest .

# Run (config is via environment variables; see .env.example for all vars)
docker run --rm -p 8000:8000 \
  -e ARANGO_ENDPOINT=https://your-arango:8529 \
  arango-tools:latest
# open http://localhost:8000
```

Health endpoints: `GET /api/health` (liveness) and `GET /api/ready` (readiness —
verifies the bundled client tools resolve). Logs are structured JSON by default
(`ARANGO_LOG_FORMAT=text` for plain text).

### Kubernetes (Helm)

A chart lives in `deploy/helm/arango-tools`:

```bash
helm install arango-tools deploy/helm/arango-tools \
  --namespace arango-tools --create-namespace \
  --set image.repository=YOUR_REGISTRY/arango-tools \
  --set image.tag=latest
```

See `deploy/helm/arango-tools/README.md` for values and constraints.

> **Single-tenant:** the backend keeps connection state in memory and spawns
> tool subprocesses, so it runs as exactly **one replica**. Deploy one release
> per team. There is **no application-level auth yet** — keep the Service
> private (the chart defaults to `ClusterIP`) or front it with your own auth
> proxy + TLS.

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
- The container runs as a non-root user with a read-only root filesystem; the
  Helm chart drops all Linux capabilities and uses the `RuntimeDefault` seccomp
  profile.
- **Not yet hardened (tracked as follow-ups):** there is no application-level
  authentication on the API/WebSocket, the connection test currently skips TLS
  certificate verification, and credentials are passed to the tools as CLI
  flags (visible via `ps` inside the pod). Until these land, rely on network
  isolation (private Service) and a single trusted tenant per deployment.
