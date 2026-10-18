# Forward routing

This page answers: how does a node delegate work to a capability it does
not possess itself, without hard-coding the target?

## What it is

Some nodes need capabilities they cannot run — a flow runner may need
`agent.ai`, a storage maintainer may need an LLM, paperless coordinates
several. Instead of binding a specific capability into that node's code,
the client node submits a task against a generic, server-side capability
called **forward** and lets the relay resolve the concrete target from
operator configuration.

The client node **does not name the target capability** in its code or
its payload. It names only itself and one of its own numbered slots.

```
Client node:  task { submitter: <self>, forward_slot: 2, ... }
                          │
                          ▼
Relay:        resolve (node=<submitter>, slot=2) → "agent.ai"
                          │
                          ▼
Scheduler:    matches "agent.ai" to a live provider node → redirects
```

Result: dependencies become configuration, not code.

## Why

- **Decoupling** — a node does not need to know *which* node or
  capability will answer; only that it needs its 2nd external dependency.
- **Re-routing without re-deploy** — changing the target
  (`agent.ai` ↔ `chat.ai`, or one provider node ↔ another) is a
  dashboard edit, not a wheel rebuild and node restart.
- **Multiple dependencies, one mechanism** — a node with 4 hard-coded
  dependencies advertises 4 numbered slots and maps each once.

## How it works

### 1. Slots (node side, node-local)

The client node **numbers its own forward slots** however it likes, as
part of its logic. Slot numbers are meaningful only in the context of the
submitting node — `paperless:1` and `storage:1` are unrelated slots.

Accepted forms: `1, 2, 3 …` (per-node counters) or `a, b, c …`
(logical labels). The task carries both:

- `submitter` — the client node (already part of the task envelope).
- `forward_slot` — the slot number for *this* dependency.

Unknown slot ⇒ relay rejects the task (never silently drops or guesses).

### 2. Mapping (operator / dashboard side)

The relay keeps a per-node, per-slot mapping table. Each row binds a
pair `(submitter node, slot)` to the concrete capability the relay should
route to.

```
submitter node │ slot │ target capability
---------------┼------┼------------------
storage-abc    │ 1    │ agent.ai
paperless-01   │ 1    │ agent.ai
paperless-01   │ 2    │ storage.archive.native
flow-runner-xy │ 3    │ agent.ai
```

Configuration lives in the **dashboard**, not in node config or code.
Editing a row changes routing immediately for subsequent tasks; it never
requires a node restart.

### 3. Redirect (relay side)

On task submit against forward, the relay looks up `(submitter, slot)`,
rewrites the task's target capability to the configured one, and processes
the task normally against that capability. From the scheduler's view it
is a normal task for `agent.ai` (or whichever target resolved); only
bookkeeping and visibility keep the dependency trace.

## Task semantics

Forwarding is a **redirect on submit**, not a second task:

- **Submitter stays** — the originating node is preserved as
  `submitted_by` (T-227 sender semantics).
- **Recipient sets owner** — whichever node claims the resolved stage
  becomes `owner_node_id` on claim, exactly like a normal capability
  stage. The relay must reject any mismatched claim (the claimed
  capability must equal the resolved target).
- **Transparent result** — from the caller's point of view the task
  completes normally against its handler; the relay's redirect is an
  internal step, reflected in observability but not in the result
  envelope.
- **No re-submission** and no second task ID — status, SSE events and
  artifact flow remain on the single task.

## Observability

- Relay logs record the redirect decision (submitter, slot, resolved target).
- Dashboards surface invalid slots as a configuration error rather than as a capability-miss.
- SSE events keep the submitter-visible lifecycle; claim/completion carry the target capability in the stage detail.

## Applicability and limits

- Forward routing depends on a valid, configured target. Unconfigured
  `(node, slot)` pairs fail at submit time — fail fast, do not fall back
  to a "default" AI capability.
- Slot numbers are per-node, not globally unique. Never combine them into
  a single `node.slot` capability name advertised by the client; the
  client advertises no new capability at all.
- Forward targets are plain capabilities: any claimable, advertised
  capability works (`agent.ai`, `storage.archive.native`, …). The relay
  performs the mapping, then the normal scheduler does the matching.

## Open design points

- Global vs. per-node slot numbering display in the dashboard
  (nodes own their numbers; relay only stores them).
- Whether redirection is visibly recorded as a stage metadata field or only
  in relay logs (observability above).
- Cascading forwards (a forwarded task whose target is itself a forwarding
  node): permitted, with a small hop limit to prevent loops.
- See [capabilities](capabilities.md) for capability naming and
  matching rules, and [tasks](tasks.md) for task/stage lifecycle.
