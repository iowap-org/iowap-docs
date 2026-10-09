# Capability

This page answers: what is a capability, how are names built, and how does
the relay match them to work?

## What it is

A **capability** is a named, typed, versioned thing a node can do — the
routing key the relay uses to match stages to nodes. It is a **label** a
node advertises, not a tool, model, or service: what happens when a node
claims a task for that capability is entirely up to the node.

```
Task: { capability: "image.generate.mflux", payload: { prompt: "fox" } }
         │
         ▼
Relay: "Which live node heartbeats image.generate.mflux?"
         │
         ▼
Node: "I do." → claims the stage → executes → completes
```

Names are lowercase, dot-separated namespaces:

| Suffix | Meaning | Example |
|--------|---------|---------|
| `.native` | Runs directly on the node, no local AI. | `storage.archive.native`, `image.generate.mflux` |
| `.ai` | Delegates to a local AI/LLM for reasoning. | `chat.ai`, `code.ai`, `agent.ai` |
| `.relay` | Relay-internal orchestration stages. | `llm.decide_cleanup.relay` |

**Names are matched exactly.** The scheduler compares the stage's
capability string with what nodes advertised in their latest heartbeat —
there is no wildcard, no fallback, and (today) no code-level enforcement of
the suffix convention: a stage requesting `db.board.create.native` is only
claimed by a node that literally advertised that string. The suffix
convention is a documented contract, so nodes without local AI advertise
every concrete capability with `.native`.

> Two `.ai` flavors exist: `chat.ai` is a stateless one-shot prompt (no
> session, tool access limited to the handler), while `agent.ai` talks to a
> persistent Hermes API server with the full toolset and multi-turn context.
> Pick `chat.ai` for quick questions, `agent.ai` for multi-step work.

## How it works

A capability is defined in the node's profile (`~/.relay/node.yaml`,
profiles under `~/.relay/profiles.d/`), published by the heartbeat, and
matched by the scheduler. The minimal entry and the fields it can carry:

```yaml
capabilities:
  - name: storage.archive.native          # required; exact-match routing key
    version: "1.0.0"                      # optional, default "1.0.0"
    type: tool                            # ai | tool | script | workflow | resource (default tool)
    description: "Compresses and archives files"
    auto_publish: true                    # include in every heartbeat
    claimable: true                       # daemon may claim stages for it
    handler: /opt/relay/handlers/archive.sh   # required when claimable: true
    max_parallel: 2                       # in-flight limit (default 1)
    timeout: 600                          # handler timeout in seconds (default 300)
    input_schema:                         # optional, documents expected payload fields
      fields:
        path:
          name: path
          type: string
          required: true
    upload_modes: [inline, artifact, bridge]   # file-transfer ladder (see below)
    result_path_hints: [answer]           # machine-readable result paths
```

| Field | Meaning |
|-------|---------|
| `name` | The routing key — matched exactly, suffix convention per above |
| `type` | How the node executes: `ai`, `tool`, `script`, `workflow`, `resource` |
| `claimable` | `true` = scheduler assigns stages; `false` = capability exists only for routes/metadata |
| `handler` | Script/command executed for claimed stages (envelope I/O — see [handler contract](../node/handlers/contract.md)) |
| `max_parallel`, `timeout` | Concurrency and time budget per stage |
| `config` | Opt-in extensions, e.g. `complete_by_script: true` |

The daemon validates profiles before publishing: duplicate names, missing
`handler` on claimable capabilities, and non-positive `max_parallel`/
`timeout` are rejected, the active profile is never touched on error. The
heartbeat forwards name, version, type, description, input_schema,
upload_modes, result_path_hints, and the computed `available`
(max_parallel vs. in-flight stages); the server stores them in the
`node_capabilities` index and resolves them as `capability_details` on
claim — a claiming handler sees the expected payload shape without an
extra discovery round-trip.

### Non-claimable capabilities

Not every capability executes tasks: `claimable: false` capabilities exist
to carry metadata or **dynamic node routes** — HTTP endpoints the relay
proxies to the node (registered on heartbeat, cleared when the node goes
offline; temp bridge routes for large-file handoff carry a TTL and a
`channel_id`). Route security is fail-closed: upstream targets outside the
node's own endpoint origin or the server allowlist are refused, loopback
and link-local targets always. Details:
[routes in the CLI reference](../node/cli.md), [storage bridge](../storage/storage.md).

### File transfer ladder

A capability that accepts or serves files declares which modes it
supports; `node-cli file send` (and the handler primitives) pick the
smallest rung that fits:

| Mode | When | Bound |
|------|------|-------|
| `inline` | base64 carried in the task payload | ≤ `max_inline_bytes` (default 5 MB) |
| `artifact` | transient relay artifact store, payload carries `artifact_id` | ≤ `max_artifact_bytes` (default 50 MB) |
| `bridge` | streamed via temp route to a storage node, payload carries `storage_ref` | larger files, RAM-bounded |

Default when `upload_modes` is undeclared: all three. Ladder bounds are
server config; the ladder itself (inline < artifact < bridge) is the
project's transfer decision — see
[artifacts](artifacts.md) and [storage](../storage/storage.md).

## What it is NOT

- **Not a tool** — a routing label; execution is the node's business.
- **Not a model** — `chat.ai` does not specify which LLM runs behind it.
- **Not a node** — a node heartbeats capabilities; one node can carry many,
  and one capability can live on many nodes (load balancing / failover).
- **Not suffix-enforced** — `.native`/`.ai`/`.relay` are convention, today
  the relay matches names without validating the suffix.

## Related pages

- [nodes](nodes.md) — the process that advertises capabilities
- [node capabilities how-to](../node/capabilities.md) — profiles, heartbeat examples, chat.ai vs agent.ai setup
- [handler contract](../node/handlers/contract.md) — the envelope I/O a claimed stage runs
- [glossary](glossary.md) — verbatim terminology