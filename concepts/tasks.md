# Tasks and Statuses

This page answers: how do tasks and stages flow through the relay, and
which statuses exist for entities?

## What it is

A **task** is a collection of one or more **stages** with dependencies — a
DAG submitted by a node or client. A **stage** is a single unit of work:
one capability, one payload, one result. The relay tracks both through a
central status registry (`core/status.py` in the iowap-server repo): every
status belongs to a **category** (`AVAILABLE`, `BUSY`, `PENDING`,
`TERMINAL`, `OFFLINE`), and business logic queries by category — new status
values can be added without touching call sites.

```
Task:   pending → accepted → running → completed/failed/timed_out/cancelled
                            ↑↓
                awaiting_subtasks / needs_input

Stage:  pending → claimed → completed/failed/timed_out
                  ↑↓  pending (released back)
        accepted ⇄ orphaned (long-run lease watchdog)
```

Because status names overlap across entity types (`pending` exists for
nodes, tasks, and stages with different transition rules), transition
checks are entity-specific (`node_can_transition`, `task_can_transition`,
`stage_can_transition`). Every transition publishes a `status_changed`
SSE event with `{entity_type, entity_id, old_status, new_status}` —
subscribe with `event_types: ["status_changed"]` to watch transitions
only.

## How it works

### Stage lifecycle

1. A pending stage is **claimed** by a node matching its capability; the
   claim lease is `claim_ttl_seconds` (default 60 s, dashboard-editable
   60–300 s without restart).
2. The node **executes** and completes the stage with a result (or an
   error dict). Handler-I/O rules: [handler contract](../node/handlers/contract.md).
3. On timeout, handler failure, or a dead node the stage is failed (up to
   `max_retries`, default 2 → 3 attempts) or released back to `pending`.

### Long-run leases and orphaned stages

Long-running capabilities use **lease extension via task notes**: the
worker keeps its lease alive by periodically noting progress. A stage
whose lease expires (default 2 h without a note) becomes `orphaned` —
deliberately **not an error**: the worker can resume it (note → back to
`accepted`), the submitter can requeue it (→ `pending`), and after 24 h
without resumption it fails. Manual takeover paths exist in the admin
API.

### Failure policy (linear)

A stage that exhausts its retries **fails its whole task** — even while
other stages are still pending. The task owner receives the `task_failed`
event on the SSE stream and can resubmit; downstream stages stay `pending`
until the owner cancels or deletes the task. The relay never cascades a
cancel. The same rule applies when a stage fails because no live node
offers its capability (orphan sweep): a busy provider keeps pending stages
alive — only a capability with **no live provider at all** fails them.

### Retry and claim gates

- `max_retries` (default 2) is applied **per stage**; each retry burns the
  budget once.
- A node claims only when its status is AVAILABLE
  (`node_can_claim`); a busy node asking for work receives
  `claimed: false` instead of an error.
- `available`, `load`, `queue_depth` in the heartbeat gate whether the
  scheduler hands out more work — `available=false` means "alive, but no
  new tasks" while the node keeps reporting results for its running
  stages.

### Node statuses (quick reference)

| Status | Category | Meaning |
|---|---|---|
| `pending` | PENDING | Registered, not yet approved |
| `approved` | AVAILABLE | Approved, no heartbeat yet |
| `online` | AVAILABLE | Heartbeating; can claim |
| `idle` | AVAILABLE | Online, explicitly available |
| `busy` | BUSY | Online, **not** claiming (manual or auto) |
| `maintenance` | BUSY | Taken out of rotation |
| `offline` | OFFLINE | Heartbeat timeout exceeded |

An approved node that goes offline comes back via heartbeat **without
re-approval** — `offline → online` is a valid transition.

## What it is NOT

- **Not a workflow engine** — the DAG has `depends_on` edges and retries,
  no conditional branching, no templates; composition across machines is
  the flow runner's job (separate node, `flow.run` capability).
- **Not a cron** — tasks run when submitted and claimed, never on a
  schedule; recurring work is the submitter's concern.
- **Not persistent storage** — a completed task's stages stay queryable,
  but artifact payloads decay (transient store — see
  [artifacts](artifacts.md)); durable copies belong on a storage node.

## Related pages

- [nodes](nodes.md) — statuses from the node's side, busy mode
- [capabilities](capabilities.md) — how stages get matched to nodes
- [handler contract](../node/handlers/contract.md) — completion and failure I/O rules
- [CLI task commands](../node/cli.md) — submit, wait, results
- [glossary](glossary.md) — verbatim terminology