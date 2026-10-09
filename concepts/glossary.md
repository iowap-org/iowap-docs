# Glossary

Verbatim terminology for the IOWAP ecosystem. Page titles and docs use
exactly these terms — humans and AI readers can rely on one vocabulary.

| Term | Meaning |
|------|---------|
| **Relay** | The coordination server; routes tasks by capability, never interprets payloads. See [overview](overview.md). |
| **Node** | A process that registers with the relay, heartbeats presence + capabilities, claims and completes stages. One node type. See [nodes](nodes.md). |
| **Capability** | A dot-separated routing key (e.g. `storage.archive.native`) a node advertises; matched by exact name. See [capabilities](capabilities.md). |
| **Capability suffix** | `.native` (no AI), `.ai` (local AI reasoning), `.relay` (relay-internal). Convention, not enforced. |
| **Stage** | A single unit of work inside a task DAG — one capability, one payload, one result. |
| **Task** | A collection of stages with `depends_on` edges, submitted by a client. |
| **DAG** | The directed acyclic graph of a task's stages. |
| **Heartbeat** | Periodic node update reporting status, load, availability, capabilities. Default every 10 s. |
| **Claim** | A node takes a pending stage matching its capabilities; the stage becomes `claimed` for up to `claim_ttl_seconds`. |
| **Complete** | A node submits a claimed stage's result (or error) to the relay. |
| **Orphaned** | Stage whose long-run lease expired (no worker notes for 2 h); resumable, no error by itself. See [tasks](tasks.md). |
| **Runtime token** (`rt_…`) | Day-to-day Bearer token per node. TTL 7 days, refreshed proactively. |
| **Registration secret** (`rs_…`) | Recovery-only credential. TTL 7 days at issue, rotated on every recovery use. |
| **Temporary token** (`tp_…`) | 24 h token issued on registration; replaced after admin approval. |
| **Master admin seed** (`adm_…`) | Emergency dashboard credential created on the relay host, stored as bcrypt hash. |
| **Bootstrap seed** (`bs_…`) | One-time 24 h session token after a master-seed dashboard login. |
| **Dashboard** | The web UI (session cookie auth) — node approval, task view, metrics. |
| **Dynamic node route** | HTTP route a node registers via heartbeat; the relay proxies authenticated requests to it. Fail-closed upstream validation. |
| **Temp bridge route** | TTL'd route tied to a `channel_id` for large-file streaming; reaped by a watchdog. |
| **Artifact** | A file in the relay's transient transfer buffer (TTL-purged), referenced as `artifact_id`. See [artifacts](artifacts.md). |
| **Transfer ladder** | `inline` (base64) < `artifact` (transient store) < `bridge` (storage node stream) — deterministic size-based mode choice. |
| **Storage node** | An external node (e.g. on a NAS) advertising storage capabilities — the durable file home. |
| **Storage ref** | Payload carrier for the `bridge` rung: `{"type", "id", "filename"}`. |
| **Handler** | External subprocess a node runs to execute a claimed stage; envelope I/O on stdin/stdout. |
| **Request/Response envelope** | `{task_id, capability, input:{…}}` in; `{status, result, error}` out — the handler I/O contract. |
| **Result path hints** | Capability-declared, machine-readable paths into the result object (e.g. `answer`) — used by flow planners. |
| **Flow** | `flow.run` capability: takes an origin task, plans subtasks, fans them out, aggregates results. A node feature, not a relay feature. |
| **Federation** | Bridging capabilities across relays (not yet implemented). See [federation](../federation/concept.md). |
| **SSE** | Server-Sent Events — the relay pushes typed events (e.g. `status_changed`, `task_failed`) on `GET /relay/v2/events/stream`. |
| **Self-care pattern** | A node without reasoning posts a decision task for a reasoning capability instead of deciding itself. |
| **node-cli** | The node's command-line tool: registration, daemon, status, tasks, files, routes. See [CLI reference](../node/cli.md). |