# arango-tools Helm chart

Deploys the single-origin Arango Tools GUI (React UI + FastAPI backend +
bundled ArangoDB client tools) into a Kubernetes cluster — the BYOC path.

## Prerequisites

- Kubernetes 1.23+
- The container image pushed to a registry your cluster can pull from
  (see the repo-root `Dockerfile`).

## Install

```bash
helm install arango-tools deploy/helm/arango-tools \
  --namespace arango-tools --create-namespace \
  --set image.repository=YOUR_REGISTRY/arango-tools \
  --set image.tag=0.1.0
```

By default the Service is `ClusterIP` (cluster-internal only). Port-forward to
reach it:

```bash
kubectl -n arango-tools port-forward svc/arango-tools 8080:80
# open http://localhost:8080
```

## Design constraints (read this)

- **Single-tenant / single replica.** The backend keeps connection state in
  memory and spawns tool subprocesses, so `replicas` is fixed at `1` and not
  configurable. Run one release per team/customer.
- **No app-level auth (yet).** Keep the Service private or front it with your
  own auth proxy + TLS. `ingress.enabled` is `false` by default.
- **Hardened pod.** Non-root (uid 10001), read-only root filesystem, all
  capabilities dropped, `RuntimeDefault` seccomp. Writable paths (`/work`,
  `/tmp`, `/home/arango`) are backed by volumes.

## Common configuration

| Key | Default | Description |
| --- | --- | --- |
| `image.repository` | `arango-tools` | Image repo |
| `image.tag` | `""` (chart appVersion) | Image tag |
| `service.type` | `ClusterIP` | Service type |
| `ingress.enabled` | `false` | Expose via Ingress (adds WS timeout annotations) |
| `connection.endpoint` | `""` | Default ArangoDB endpoint (optional) |
| `connection.database` | `_system` | Default database |
| `connection.username` | `root` | Default username |
| `connection.password` | `""` | Inline password (stored in a generated Secret) |
| `connection.existingSecret` | `""` | Use an existing Secret instead |
| `connection.passwordKey` | `ARANGO_PASSWORD` | Key within the Secret |
| `workDir.persistence.enabled` | `false` | Persist tool output across restarts (PVC) |
| `resources` | 100m/256Mi … 1/1Gi | Requests/limits |

### Password via an existing Secret

```bash
kubectl -n arango-tools create secret generic arango-db \
  --from-literal=ARANGO_PASSWORD='s3cret'

helm install arango-tools deploy/helm/arango-tools \
  --set connection.existingSecret=arango-db
```

## Validate locally

```bash
helm lint deploy/helm/arango-tools
helm template arango-tools deploy/helm/arango-tools
```
