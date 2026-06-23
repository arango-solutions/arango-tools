# syntax=docker/dockerfile:1

# Multi-stage build for the Arango Tools GUI (single-origin BYOC image).
#
#   1. frontend-build : compile the React/Vite UI into static assets
#   2. runtime        : Debian slim + ArangoDB client tools + the FastAPI backend,
#                       serving the built UI from the same origin.
#
# The image bundles the ArangoDB *client* tools (arangodump, arangorestore, …)
# so the binaries are always present and version-matched. Pin the tools to the
# server versions you support via the ARANGODB_REPO build arg.

# ---------------------------------------------------------------------------
# Stage 1: build the frontend
# ---------------------------------------------------------------------------
FROM node:20-slim AS frontend-build

WORKDIR /frontend
# Install deps first for better layer caching.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build   # -> /frontend/dist

# ---------------------------------------------------------------------------
# Stage 2: runtime (backend + bundled client tools + built UI)
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Which ArangoDB client package repository to use. Override to match the server
# versions you support, e.g. --build-arg ARANGODB_REPO=arangodb312.
ARG ARANGODB_REPO=arangodb312
# uv version is pinned for reproducible dependency resolution.
ARG UV_VERSION=0.11.7

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Where the client tools land and where the built UI is served from.
    ARANGO_TOOLS_BIN=/usr/bin \
    ARANGO_STATIC_DIR=/app/frontend/dist \
    PATH="/app/backend/.venv/bin:${PATH}"

# Install the ArangoDB client-only tools (no server, no Starter).
# NOTE: ArangoDB's package-signing GPG key is currently expired upstream, so apt
# rejects the repo's signature. We pull the repo over HTTPS and mark it
# [trusted=yes] (transport security via TLS to the official domain) instead of
# relying on the expired key. Pin a concrete package version for reproducible,
# auditable builds once you've chosen the supported ArangoDB version.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    echo "deb [trusted=yes] https://download.arangodb.com/${ARANGODB_REPO}/DEBIAN/ /" \
        > /etc/apt/sources.list.d/arangodb.list; \
    apt-get update -o Acquire::AllowInsecureRepositories=true; \
    apt-get install -y --no-install-recommends --allow-unauthenticated arangodb3-client; \
    rm -rf /var/lib/apt/lists/*

# Bring in the uv package manager (pinned).
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

WORKDIR /app/backend

# Resolve dependencies first (cached unless the lockfile changes).
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the application itself.
COPY backend/ ./
RUN uv sync --frozen --no-dev

# Bring in the built frontend.
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Run as a non-root user. Create a writable working dir for tool output
# (dump/import/export) that can be backed by a volume in Kubernetes.
RUN useradd --system --uid 10001 --create-home --home-dir /home/arango arango \
    && mkdir -p /work \
    && chown -R arango:arango /work /app
USER arango
WORKDIR /work

EXPOSE 8000

# Liveness/readiness without depending on curl being present.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
