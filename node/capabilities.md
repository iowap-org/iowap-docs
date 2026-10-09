# Capabilities — How-To for Node Operators

Defining, validating, and publishing capability profiles on a node. The
model (routing, suffixes, ladder): [concept: capability](../concepts/capabilities.md).
Full CLI flags: [CLI reference](cli.md).

## Profile anatomy

```bash
mkdir -p ~/.relay/profiles.d
cat > ~/.relay/profiles.d/default.yaml <<'YAML'
capabilities:
  - name: chat.ai
    version: "1.0.0"
    type: ai
    description: "General conversational AI."
    auto_publish: true          # include in every heartbeat
    claimable: true             # daemon may claim stages for it
    handler: /opt/relay/handlers/chat-ai.sh
    max_parallel: 2
    timeout: 300
    input_schema:
      fields:
        prompt:
          name: prompt
          type: string
          required: false
          description: "The instruction or question."
YAML

node-cli capabilities validate default   # never touches the active profile
# -> profile is valid
node-cli capabilities publish default    # atomic write to node.yaml
# -> published (daemon picks it up at the next heartbeat or via SIGHUP)
```

Publish flow:

```
Operator edits profiles.d/default.yaml
        ↓
node-cli capabilities validate default    ← validates without touching active
        ↓
node-cli capabilities publish default     ← atomic write to node.yaml + SIGHUP
        ↓
Daemon heartbeats the new capabilities (or reloads on SIGHUP)
```

A minimal profile without any capability is valid — node-level fields
only ([config](config.md)).

## The handler

A handler is an external subprocess the daemon runs for claimed stages.
Its contract (stdin envelope in / stdout envelope out, exit codes,
timeout, env vars like `RELAY_TASK_ID`): normative in
[handler contract](handlers/contract.md). The daemon captures stderr into
its log — never sent to the relay as the result.

A capability that moves files declares its allowed transfer modes:

```yaml
- name: storage.store.native
  upload_modes: [inline, artifact, bridge]
  input_schema:
    fields:
      path: { name: path, type: string, required: true }
```

Narrow nodes restrict the ladder (`upload_modes: [inline]`) — too-big
files are refused instead of falling into a mode the handler can't
process.

## `chat.ai` vs `agent.ai`

Both are `.ai` reasoning capabilities; the difference is the execution
backend:

| | `chat.ai` | `agent.ai` |
|---|---|---|
| Backend | `hermes -z` (subprocess) | Hermes API Server (HTTP) |
| Session | none — one-shot | persistent, multi-turn |
| Tools | limited to what `-z` provides | full Hermes toolset |
| Use for | quick stateless questions ("What time is it?") | multi-step work ("update the worker, restart the daemon") |
| Latency | higher (process start each call) | lower (server stays running) |

```yaml
- name: agent.ai
  type: ai
  description: "Full Hermes agent with persistent session and all tools."
  auto_publish: true
  claimable: true
  handler: /opt/relay/handlers/agent-handler.sh
  max_parallel: 1
  timeout: 600
  input_schema:
    fields:
      task:
        name: task
        type: string
        required: true
        description: "The task description for the agent to execute."
```

The `agent-handler.sh` POSTs to the local Hermes API Server
(`http://localhost:8642/v1/chat/completions`, Bearer `API_SERVER_KEY`,
started via `hermes gateway`) instead of spawning `hermes -z`. Any
OpenAI-compatible frontend can point at the same server. Full server
docs: [Hermes API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server).

## Dynamic node routes

A capability can carry a `routes:` block — HTTP endpoints the relay
proxies to the node (registered on heartbeat, cleared when the node goes
offline):

```yaml
- name: inventory.pages
  version: "1.0.0"
  claimable: false
  routes:
    - path: /api/task-submit
      method: POST
      auth: session
      upstream: /api/task-submit        # path (resolved against the node's endpoint — recommended) or absolute URL
      description: "Submit an inventory task"
```

| Route field | Required | Meaning |
|-------------|----------|---------|
| `path` | yes | Sub-path under `/relay/v2/dashboard/api/node-routes/<node_id>/…`; `{id}` params supported |
| `method` | yes | `GET`, `POST`, `PUT`, `PATCH` — `DELETE` is reserved for unregistering |
| `auth` | no | `session` (default; dashboard cookie + `dashboard:view`), `node_token` (Bearer), `none` (public — careful) |
| `upstream` | yes | Path (node's own endpoint origin) or absolute URL on an allowed host |

Security is fail-closed: upstreams outside the node's own endpoint origin
or the server's allowlist are refused; loopback/link-local/cloud-metadata
always. `DELETE` upstreams must be registered under another method.

### Temp bridge routes (time-boxed)

Permanent routes are replaced on every heartbeat. For large-file handoff
the ladder uses **temp routes**: TTL-capped (default 24 h), tied to a
`channel_id`, restricted to `/upload/`/`/download/` paths, reaped by a
watchdog:

```bash
node-cli route register --path /upload/x --method POST \
    --upstream http://192.0.2.55:8791/upload/x \
    --ttl 3600 --channel ch_x
node-cli route unregister --path /upload/x --method POST
node-cli route list    # only this node's own routes
```

The full storage-channel flow (who calls what, streaming hop by hop):
[storage](../storage/storage.md).

## Verification

```bash
node-cli capabilities current
# -> current profile: default
node-cli heartbeat --json | python3 -m json.tool | head
# -> capabilities list as sent to the relay (identity + metadata)
node-cli capabilities server --json    # what the server has stored for this node
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `403` on claim | profile not published / `auto_publish: false` — `capabilities diff`, then `publish` |
| publish rejected | duplicate names, claimable without handler, bad types — fix the error the validator names |
| handler never runs | `handler` path missing or not executable on the node host |
| routes dead after restart | routes live on heartbeat — node must be online; nothing to re-register manually |
| profile lost after daemon update | re-publish the working profile (`profiles.d/` survives) |

## Related pages

- [config](config.md) — where profiles live, daemon transport
- [handlers](handlers/contract.md) — the I/O the handler implements
- [operations](operations.md) — daemon control
- [glossary](../concepts/glossary.md) — terminology