# Node

This page answers: what is a node in IOWAP, and what does every node do —
regardless of capability?

## What it is

A **node** is a process that connects to the relay, heartbeats its presence,
and offers capabilities. There is only **one node type** — what makes a node
useful are the capabilities it heartbeats (see
[capabilities](capabilities.md)). A node without capabilities is just a
heartbeat: present but idle.

```
┌─────────────────────────────────────────────┐
│  Node                                        │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │  Core (every node)                   │   │
│  │  • Register with the relay           │   │
│  │  • Heartbeat presence + status       │   │
│  │  • Manage token lifecycle            │   │
│  │  • Claim + complete tasks            │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │  Capabilities (what differs)         │   │
│  │  • chat.ai          → LLM chat       │   │
│  │  • image.gen.mflux  → image gen      │   │
│  │  • storage.archive  → archive files  │   │
│  │  • federation       → bridge relays  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## How it works

Every node follows the same lifecycle:

```
register → poll approval → heartbeat → claim → execute → complete
```

1. **Register** via `POST /relay/v2/auth/register` → the node receives a
   `node_id` (8 characters from an unambiguous alphabet, e.g. `3P4KEWGE`),
   a temporary token, and a registration secret.
2. **Wait for approval** — an admin activates the node in the dashboard or
   via the admin API; the node polls `POST /relay/v2/auth/status`.
3. **Heartbeat** every `heartbeat_interval_seconds` (default **10 s**) →
   the status moves from `approved` to `online`. A node that stays silent
   for `intervals × heartbeat_timeout_multiplier` (default 5 × 10 s = 50 s)
   is marked `offline`.
4. **Claim** a stage matching one of its capabilities.
5. **Execute** the action described in the stage payload.
6. **Complete** by submitting the result (or an `error` dict) to the relay.

The heartbeat carries status, load (normalised 0–100), `available`,
`queue_depth`, capabilities, and human-readable node metadata. **One runtime
token per node** — refreshing it invalidates the previous one; refresh and
recovery flows are described in [token operations](../node/tokens.md).

### Statuses

| Status | Category | Meaning | Claims / reports |
|---|---|---|---|
| `pending` | PENDING | Registered, not yet approved | no / no |
| `approved` | AVAILABLE | Approved, no heartbeat yet | yes / yes |
| `online` | AVAILABLE | Sent at least one heartbeat | yes / yes |
| `idle` | AVAILABLE | Online, explicitly available | yes / yes |
| `busy` | BUSY | Online, not accepting new claims | no / yes |
| `maintenance` | BUSY | Taken out of rotation manually | no / yes |
| `offline` | OFFLINE | Missed too many heartbeats | no / no |

*Claims* means accepting new work (AVAILABLE nodes only). *Reports* means
completing stages, sending notes, and using artifact/storage routes — every
live node (AVAILABLE or BUSY) keeps doing that, so a busy node finishes its
running work and keeps its lease alive. `online` + `available=false` means
"alive but do not send tasks right now". A provider can also disable a
single capability per heartbeat (`"available": false` on the capability) —
siblings stay available. Full status system: [tasks](tasks.md).

### Busy mode (manual + automatic)

- **Manual:** `node-cli node busy` / `node idle` / `node clear-status` —
  the request persists in the node state file and rides every heartbeat.
- **Automatic (load):** at or above its `load_cap` for
  `auto_busy_consecutive_heartbeats` (default 3) consecutive heartbeats →
  `busy`; back below the cap → `idle` again.
- **Automatic (GPU):** with `queue_depth >= 1` a node flips to `busy`
  immediately regardless of CPU load — a machine running one FLUX/MLX job
  must not be handed a second one just because the CPU is idle. It reverts
  when the queue drains *and* load is below the cap.

## What it is NOT

- **Not a machine** — a single host can run many nodes.
- **Not a process type** — there is no "worker" vs "federation" node class.
  There is only **node**; capabilities define what it does.
- **Not tied to a capability** — a node can change its capabilities at
  runtime by heartbeating a different set.
- **Not a relay** — a node connects to a relay; it does not route tasks
  itself.

## Related pages

- [capabilities](capabilities.md) — the routing keys nodes advertise
- [node setup](../node/setup.md) — install, register, run the daemon
- [node operations](../node/operations.md) — daemon and status management
- [glossary](glossary.md) — verbatim terminology

> **Scaling note:** designed for single-server, small-to-medium clusters —
> tens of nodes, hundreds of tasks per minute; SQLite with WAL handles that
> comfortably. Larger deployments: see
> [server/database](../server/database.md).