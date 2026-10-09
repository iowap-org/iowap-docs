# API Reference

All endpoints live under the `/relay/v2` prefix (the v2 router) except
`/health`, `/ready`, and `/metrics` at the root. Most node-facing
endpoints require a `rt_…` runtime token in the `Authorization: Bearer`
header; dashboard API endpoints require a signed session cookie.

Machine-readable spec: **`openapi.json`** at the relay root —
`http://<relay>:8788/openapi.json` lists every registered route with its
schema (routes marked `include_in_schema=false` in code are excluded; the
dashboard internals below appear there as well).

Concepts behind the endpoints: [overview](../concepts/overview.md).
Node-side usage: [node setup](../node/setup.md).

## Health & Observability — root

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | none | Liveness (process up) |
| GET | `/ready` | none | Readiness — probes database, maintenance loop; returns `{"status": "ready"\|"degraded", "database", "scheduler", "maintenance_age_seconds", "maintenance_last_ok"}` — the event bus is deliberately **not** probed (it is always available in-process, a subscriber count says nothing about relay health) |
| GET | `/metrics` | none | Prometheus text — auth-failure counters, node/task/stage gauges, latency histograms, retry ratio, per-node load/queue, throughput |

Detail pages: [observability](../concepts/observability.md).

## Auth — `/relay/v2/auth`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/relay/v2/auth/register` | none | Register a worker/service node → `node_id`, temporary token, registration secret |
| POST | `/relay/v2/auth/register-admin` | bootstrap seed `adm_…` | Register an admin node directly with a runtime token |
| POST | `/relay/v2/auth/refresh` | `rt_…` or `rs_…` | Rotate the runtime token or the registration secret |
| POST | `/relay/v2/auth/status` | read-only | Report credential lifetimes; pending nodes may poll with the registration secret |

Token families: [tokens](../concepts/tokens.md).

## Discovery — `/relay/v2/discovery`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/relay/v2/discovery/heartbeat` | `rt_…` | Heartbeat with status, load, queue_depth, capabilities (merge mode) |
| POST | `/relay/v2/discovery/worker-heartbeat` | `rt_…` | Full-replace variant — publishes the node's complete authoritative capability set |
| GET | `/relay/v2/discovery/nodes` | `rt_…` | List known nodes |
| GET | `/relay/v2/discovery/query` | `rt_…` | Query the capability registry |
| GET | `/relay/v2/discovery/capabilities` | `rt_…` | All advertised capabilities (aggregate `available` over live providers) |
| GET | `/relay/v2/discovery/capabilities/{name}` | `rt_…` | Capability detail (incl. `upload_modes`, `input_schema`) |
| GET | `/relay/v2/discovery/transfer-config` | `rt_…` | Transfer-ladder bounds: `{max_inline_bytes, max_artifact_bytes, max_payload_bytes}` |

Heartbeat body reference: [worked examples](#worked-examples-curl) below.

## Scheduler — `/relay/v2/scheduler`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/relay/v2/scheduler/tasks` | `rt_…` | Submit a task DAG |
| GET | `/relay/v2/scheduler/tasks` | `rt_…` | List tasks |
| GET | `/relay/v2/scheduler/tasks/{task_id}` | `rt_…` | Task detail (stages, artifacts, notes) |
| POST | `/relay/v2/scheduler/task-simple` | `rt_…` | Submit a single-stage task |
| POST | `/relay/v2/scheduler/claim` | `rt_…` | Claim one pending stage — response includes `capability_details` when metadata was advertised |
| POST | `/relay/v2/scheduler/stages/{stage_id}/complete` | `rt_…` | Complete a claimed stage with a result dict |
| POST | `/relay/v2/scheduler/tasks/{task_id}/notes` | `rt_…` | Append a note (1–2000 chars) — the long-run lease keeps alive via notes |
| POST | `/relay/v2/scheduler/artifacts/{task_id}` | `rt_…` | Associate artifacts with a task |
| GET | `/relay/v2/scheduler/artifacts/{task_id}` | `rt_…` | List task artifacts |
| DELETE | `/relay/v2/scheduler/artifacts/{artifact_id}` | `rt_…` | Remove an artifact association |

Status gates: reporting routes (completion, notes, artifacts, storage)
accept any live node — `approved`/`online`/`idle`/`busy`/`maintenance`
— so a busy node finishes running work and keeps its lease alive. `claim`
accepts busy nodes too and answers `{"claimed": false}` (HTTP 200) when
nothing matches or the node may not claim — the claim route has no 403
path; eligibility is encoded in `claimed`. Task submission
and read-only task routes stay approved/online-only (a `403` there can
mean "busy"). Policies per entity:
[tasks](../concepts/tasks.md).

## Presence — `/relay/v2/presence`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/relay/v2/presence/update` | `rt_…` | Update presence (informational) |
| GET | `/relay/v2/presence/nodes` | `rt_…` | List presence records |
| GET | `/relay/v2/presence/{node_id}` | `rt_…` | One node's presence record |

## Events — `/relay/v2/events`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/relay/v2/events/stream` | `rt_…` (`?node=<own id>`; `types` filter optional) | SSE stream |

The bus publishes: `task_created`, `task_completed`, `task_failed`,
`stage_claimed`, `stage_completed`, `stage_failed`, `status_changed`
(payload `{entity_type, entity_id, old_status, new_status}`),
`node_online`, `node_offline`, `presence_changed`, `artifact_created`,
`artifact_deleted`.

Server-side filtering via `types` is **whitelisted** and narrower:
`node_online`, `node_offline`, `task_created`, `stage_claimed`,
`stage_completed`, `presence_changed`, `artifact_created` — any other
value answers `400 Unknown event types`. The filtered stream is meant for
daemon-style consumers; everything else arrives unfiltered.

## Storage — `/relay/v2/storage`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/relay/v2/storage/upload` | `rt_…` | Upload a file as an artifact (multipart, default limit 100 MiB) |
| GET | `/relay/v2/storage/files/{artifact_id}` | `rt_…` | Download an artifact (efficient streaming response) |
| GET | `/relay/v2/storage/files/{artifact_id}/meta` | `rt_…` | Artifact metadata |
| DELETE | `/relay/v2/storage/files/{artifact_id}` | `rt_…` | Delete an artifact |
| GET | `/relay/v2/storage/list` | `rt_…` | List artifacts (`?task_id=…`) |
| POST | `/relay/v2/storage/chunked/init` | `rt_…` | Start a chunked upload |
| POST | `/relay/v2/storage/chunked/{upload_id}/chunk` | `rt_…` | Upload one chunk |
| POST | `/relay/v2/storage/chunked/{upload_id}/complete` | `rt_…` | Finalise a chunked upload |

Ladder context: [artifacts](../concepts/artifacts.md). Durable files
belong on a storage node ([storage](../storage/storage.md)) — the relay
store is transient.

## Cluster — `/relay/v2/cluster`

Public, privacy-safe views (no auth) — they never expose tokens, secrets,
emails, or password hashes; the synthetic dashboard-admin node is
excluded:

| Method | Path | Purpose |
|---|---|---|
| GET | `/relay/v2/cluster/overview` | Cluster summary: counts, compact node list, queue/task stats |
| GET | `/relay/v2/cluster/nodes` | Public node directory |
| GET | `/relay/v2/cluster/nodes/{node_id}` | Public node profile (incl. load history) |
| GET | `/relay/v2/cluster/users` | Pseudonymised user directory |
| GET | `/relay/v2/cluster/users/{user_id}` | Public user profile |
| GET | `/relay/v2/cluster/activity` | Recent activity events (`?limit=1–200`, default 50) |

## Dynamic node routes — `/relay/v2/dashboard/api/node-routes`

Node-declared proxy endpoints (heartbeat-registered; temp bridge routes
TTL'd). Auth column: what a **caller** needs — node-facing self-management
runs with the node's `rt_…` Bearer.

| Method | Path | Caller auth | Purpose |
|---|---|---|---|
| GET | `/…/node-routes` | `rt_…` (node) | List the calling node's own routes |
| POST | `/…/node-routes/register` | `rt_…` (node) | Register a temp route (`path`, `method`, `ttl_seconds`, `upstream`, `channel_id`) |
| DELETE | `/…/node-routes/{node_id}/{path}` | `rt_…` (node, `?method=`) | Revoke a temp route before TTL |
| GET/POST/PUT/PATCH | `/…/node-routes/{node_id}/{rest_of_path}` | per route `auth` (`session` / `node_token` / `none`) | Proxy to the node's upstream (streaming, chunkwise) |

`DELETE` is reserved for unregistering — a node exposing a DELETE
upstream registers it under another method. Upstream validation is
fail-closed (node endpoint origin / allowlist; loopback etc. refused).
Details: [capabilities how-to](../node/capabilities.md),
[storage bridge](../storage/storage.md).

## Dashboard — `/relay/v2/dashboard`

Session-cookie auth for account/admin routes unless noted. The home
page serves the **public Community Dashboard** (no auth); UI pages and
their JSON API:

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/relay/v2/dashboard/` | none | Home (public Community Dashboard) |
| GET | `/relay/v2/dashboard/admin` | session | Admin overview page |
| GET | `/relay/v2/dashboard/node/{node_id}` | session | Node profile page |
| GET | `/relay/v2/dashboard/user/{user_id}` | session | User profile page |
| GET/POST | `/relay/v2/dashboard/login` | none | Login page / authenticate |
| GET | `/relay/v2/dashboard/bootstrap` | none | First-admin page (master seed) |
| POST | `/relay/v2/dashboard/api/bootstrap` | master seed | Create the first human admin |
| POST | `/relay/v2/dashboard/logout` | session | Clear session |
| GET | `/relay/v2/dashboard/change-password` | session | Forced password change |
| GET | `/relay/v2/dashboard/api/me` | session | Current user |
| POST | `/relay/v2/dashboard/api/me/password` | session | Change own password |
| GET | `/relay/v2/dashboard/api/overview` | session | Cluster overview JSON |
| GET | `/relay/v2/dashboard/api/events/recent` | session | Recent events |
| GET | `/relay/v2/dashboard/api/endpoints` | session | List exposed v2 endpoints (info view) |
| GET | `/relay/v2/dashboard/api/capabilities` | session | Capabilities advertised by online nodes |
| GET | `/relay/v2/dashboard/api/transfer-status` | session | Transfer-ladder config + bridge-availability |
| POST | `/relay/v2/dashboard/api/transfer-config` | session | Edit transfer-ladder bounds (admin UI sliders) |
| POST | `/relay/v2/dashboard/api/task-submit` | session | Submit a task from a node page |
| GET | `/relay/v2/dashboard/api/tasks/{task_id}` | session | Task detail for the tasks view |
| GET | `/relay/v2/dashboard/api/permissions` | session | Permission catalog |
| GET/POST | `/relay/v2/dashboard/api/users` · `/users/{id}/…` | session | User management (list/create/groups/password/active/delete) |
| GET/POST | `/relay/v2/dashboard/api/groups` · `/groups/{id}/permissions` | session | Group/permission management |
| GET | `/relay/v2/dashboard/api/metrics` | session | Metrics JSON for the built-in page |
| GET/POST | `/relay/v2/dashboard/api/scheduler-config` | session (system:config) | Claim settings (`claim_ttl_seconds` 60–300, `max_retries` 0–10) — live without restart |
| GET | `/relay/v2/dashboard/metrics` | session | Metrics page (HTML) |
| GET | `/relay/v2/dashboard/static/{filename}` | none | Static assets |

## Admin — `/relay/v2/admin`

Admin runtime token required:

| Method | Path | Purpose |
|---|---|---|
| GET | `/relay/v2/admin/nodes` | List all nodes |
| POST | `/relay/v2/admin/nodes/{node_id}/approve` | Approve pending node → issues runtime token |
| POST | `/relay/v2/admin/nodes/{node_id}/token` | Issue new runtime token (invalidates previous) |
| DELETE | `/relay/v2/admin/nodes/{node_id}` | Delete node + records |

## Docs — `/relay/v2/docs`

Serves every Markdown page in the docs tree as HTML — discovered
mechanically (flat slugs: path relative to `docs/`, `/` joined with `-`).
No code change needed to add a page; legacy short names keep resolving.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/relay/v2/docs` | none | JSON index of served documents |
| GET | `/relay/v2/docs/{slug}` | none | Render one document as HTML |

That's what `node-cli docs` consumes.

## Worked examples (cURL)

Examples use `export RELAY_HOST=<relay-host>`, default port 8788, jq for
readability. Full error-code table and common responses:

| Status | Meaning | Typical cause |
|---|---|---|
| `400` | Bad request | Malformed JSON, missing field, payload too large |
| `401` | Unauthorized | Missing/invalid/expired token |
| `403` | Forbidden | Valid token, not allowed (pending node, non-admin) |
| `404` | Not found | Unknown id |
| `409` | Conflict | Duplicate `node_name`/`node_id` |
| `413` | Payload too large | Above `max_upload_bytes` |
| `422` | Validation error | Pydantic field errors in `detail` |
| `429` | Rate limit | `register` 10/min, `register-admin` 5/min, `refresh`/`status` 30/min |
| `500` | Internal | Relay bug — journal |

Error body shape: `{"detail": "…"}`.

### Register a node

```bash
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "node_name": "my-node",
    "endpoint": null,
    "role": "service",
    "capabilities": [{"name": "storage.archive.native", "version": "1.0.0"}]
  }' | jq
# -> {"node_id": "...", "status": "pending", "token": "tp_...", "registration_secret": "rs_...", ...}
```

Errors: `409` name exists; `422` malformed capabilities.

### Register an admin node (master seed)

```bash
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/auth/register-admin" \
  -H "Content-Type: application/json" \
  -d '{"node_name": "admin-cli", "bootstrap_secret": "adm_...", "endpoint": null,
       "capabilities": [{"name": "admin", "version": "1.0.0"}]}' | jq
# -> {"token_type": "runtime", "token": "rt_...", "status": "approved"}
```

### Heartbeat

```bash
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/discovery/heartbeat" \
  -H "Authorization: Bearer rt_..." \
  -H "Content-Type: application/json" \
  -d '{
    "available": true, "load": 0.0, "queue_depth": 0,
    "capabilities": [{"name": "storage.archive.native", "version": "1.0.0"}]
  }' | jq
# -> {"node_id": "...", "status": "ok"}
```

Optional body fields: `status` (operator request, e.g. `busy`),
`load_cap` (per-node ceiling — `load >= load_cap` for 3 consecutive
heartbeats auto-busies the node), `endpoint`, `node_name`, `description`,
`routes`.

### Claim + complete

```bash
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/scheduler/claim" \
  -H "Authorization: Bearer rt_..." -H "Content-Type: application/json" \
  -d '{"capability": "storage.archive.native"}' | jq
# -> {"claimed": true, "stage": {...}}   |   {"claimed": false, "stage": null} (200)

curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/scheduler/stages/<stage_id>/complete" \
  -H "Authorization: Bearer rt_..." -H "Content-Type: application/json" \
  -d '{"result": {"status": "archived", "bytes": 1234567}}' | jq
# -> {"ok": true, "stage_id": "...", "status": "completed"}
```

Errors: claim `403` capability not advertised; complete `404` unknown
stage, `409` not claimed by this node / already completed.

### Submit tasks

```bash
# Single stage:
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/scheduler/task-simple" \
  -H "Authorization: Bearer rt_..." -H "Content-Type: application/json" \
  -d '{"capability": "chat.ai", "payload": {"prompt": "What is the time in Tokyo?"},
       "name": "tokyo-time", "priority": 3}' | jq
# -> {"task_id": "...", "stage_id": "...", "status": "pending"}

# Pin to a specific node:
#   add "owner_node_id": "<node_id>" to either form

# Full DAG:
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/scheduler/tasks" \
  -H "Authorization: Bearer rt_..." -H "Content-Type: application/json" \
  -d '{
    "task_name": "archive-and-notify", "priority": 3,
    "stages": [
      {"stage_name": "archive", "capability": "storage.archive.native",
       "payload": {"file_name": "report.pdf", "target_path": "/nas/archive"}},
      {"stage_name": "notify", "capability": "chat.ai", "depends_on": ["archive"],
       "payload": {"message": "Archive completed"}}
    ]}' | jq
```

Errors: `422` (payload > max, priority out of 0–10); `404` unknown
`depends_on` id.

### Upload / download an artifact

```bash
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/storage/upload" \
  -H "Authorization: Bearer rt_..." \
  -F "file=@/tmp/report.pdf" -F "task_id=<task_id>" | jq
# -> {"artifact_id": "...", "size_bytes": ..., ...}   |  413 > 100 MiB

curl -s -X GET "http://${RELAY_HOST}:8788/relay/v2/storage/files/<artifact_id>" \
  -H "Authorization: Bearer rt_..." -o /tmp/report.pdf
# streams in 64 KiB chunks; metadata-only: .../files/<artifact_id>/meta
```

### Refresh / recover a token

```bash
# Rotate runtime token (old invalidated immediately):
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/auth/refresh" \
  -H "Authorization: Bearer rt_..." -H "Content-Type: application/json" \
  -d '{"requested_credential": "runtime_token"}' | jq

# Recover a lost runtime token (no Bearer; rotates the registration secret too):
curl -s -X POST "http://${RELAY_HOST}:8788/relay/v2/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "...", "registration_secret": "rs_...",
       "requested_credential": "runtime_token"}' | jq
# -> {"token": "rt_...", "expires_at": "...", "message": "...rotated"}
```

Errors: `401` secret invalid/expired; `403` node not approved; `404`
unknown node. Flows: [token operations](../node/tokens.md).

## Related pages

- [overview](../concepts/overview.md) — architecture
- [node CLI reference](../node/cli.md) — the client-side commands
- [observability](../concepts/observability.md) — metrics meaning
- [glossary](../concepts/glossary.md) — terminology