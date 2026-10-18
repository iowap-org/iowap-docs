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

### Node-level top-level keys

The active profile also carries node-level configuration as top-level
keys (unknown top-level keys pass validation; only unknown keys *inside*
a capability block are rejected):

- `status` — operator busy/idle state, managed by
  `node-cli node busy|idle|clear-status` (the CLI edits the active YAML
  as text and preserves the rest of the document verbatim).
- `node_name`, `description` — node overrides.
- `node_cli_path` — **maintained by node-cli itself** (since wheel
  2.3.20, T-226): every invocation and the daemon start stamp their own
  absolute console-script path as the top-level key; `capabilities
  publish` re-stamps after its byte-exact copy. The write is
  drift-guarded (no mtime churn while the value matches) and
  text-preserving. Consumers that cannot rely on `PATH` (a desktop
  gateway, a session bridge) read this key first, then fall back to
  `PATH` and known install locations. Treat any other top-level key as
  operator config: put it into the working profile in `profiles.d/`, not
  into the active file by hand.

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

## Forward slots (forward routing)

A node sometimes needs a dependency it cannot name: it only knows
"my slot 2 must be processed". Forward routing (T-Forward) solves this —
the task is submitted against the relay's `forward` pseudo-capability and
carries a node-local **slot**; the relay resolves
`(this node, slot) → target capability` from its forward-mapping table
(operator-configured in the dashboard) and redirects the task submit-time.
The client never names the target capability, and the redirect never
changes the resulting `task_id`.

Slot numbers are **per-node only**: `1` on your node and `1` on another
node may mean different things. Keep your node's numbering as operational
notes (node-side only, no config schema — the block below is NOT read,
validated, or heartbeated anywhere):

```yaml
# node-side only, operational notes — does NOT get heartbeated
forward_slots:
  1: agent-decision        # maintenance decision
  2: artifact-processing   # storage archive
  3: knowledge-summarize   # flow builder helper
```

Rules:

- Slots never leave the node's own bookkeeping: the node never converts a
  slot into a capability name and never advertises anything for it.
- The `forward` pseudo-capability is **never advertised** by a node: a
  profile declaring a capability named `forward` is rejected by
  `node-cli capabilities validate` / `publish`.
- Heartbeat, handlers, and the daemon are untouched — a redirected task
  behaves like any normal task of the resolved target. The claiming
  handler receives the **resolved** capability and a payload without the
  slot (the relay strips `forward_slot` on redirect).

### Usage

```bash
# "I need my dependency 2" — the relay resolves the target capability:
node-cli task submit --stage 'agent.ai:{"prompt": "gate decision please"}' --forward-slot 2
```

`--forward-slot` replaces the `--stage` capability with `forward` and
carries the slot inside the payload (`"forward_slot": "2"`). The same
works without the flag by submitting capability `forward` with a
`forward_slot` key in the stage payload; an explicit `--forward-slot`
wins over a payload-carried key.

Slots are strings: numeric (`2`) or lexical (`a…z`, `arch-1` style),
1..64 chars from `A-Za-z0-9_-` (no whitespace, no dots). The task-simple
one-liner flow supports the flag.

### Relay refusals (surfaced verbatim, never retried)

The CLI prints the relay's error body verbatim, adds an actionable hint
for the codes below, and exits `1` — forward refusals are configuration
problems, so they are never retried automatically.

| Error | Meaning | Fix |
|---|---|---|
| `422 forward_mapping_missing` | no mapping for `(node, slot)` | open the relay dashboard (node profile → Forward mappings) and configure the mapping |
| `422 forward_mapping_invalid` | slot malformed/too long | do **not** retry — fix the slot value or the mapping |
| `404 forward_node_unknown` | submitter node not registered | `node-cli node register` again |
| `422 target_unknown_capability` | mapping target not in the capability catalog | stale mapping — ask the operator to update it |
| `400 redirect_self` | mapping points at `forward` itself | operator must fix the mapping target |

Against an older relay (pre-forward-routing) a forward submit fails with
`404 Capability 'forward' not found` — the client has no feature flag for
this; the message is self-explanatory.

The server-side story (mapping management, semantics, dashboard UI):
[Forward routing concepts](../concepts/forward-routing.md).

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