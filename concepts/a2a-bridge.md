# Agent-to-Agent (A2A) Bridge

This page answers: how do agents talk to each other through the IOWAP fabric,
and what is the minimal contract?

## What it is

An **A2A bridge** lets two agents exchange messages over the IOWAP fabric
without a dedicated chat network. The transport is the existing
**bridge-adapter file contract**, the reply path is the existing **task
system**:

- **The inbox is the ear.** Agent *B* publishes one capability, `a2a.inbox`.
  It does nothing but receive messages: every message lands in a file folder
  that a bridge adapter owns.
- **The task is the voice.** When *B* replies, it does not call a special
  "send" API — it writes a file into its *outbox* and lets the wrapper
  submit a **new task** back to *A*, addressed to *A*'s `a2a.inbox`, with
  `reply_to` pointing at the original message id.

```
Agent A                         Agent B
  │  task submit a2a.inbox:      │
  │  {from, text}               │
  │                              │   handler -> requests/<id>.json (wrapper feed)
  └─────────────────────────────▶   wrapper -> inbox/a2a/<id>.json
                                 agent reads it, writes reply
                                 outbox/a2a/<reply-id>.json
                                 wrapper send-hook:
                                   task submit a2a.inbox {reply_to} ──▶ Agent A
```

There is deliberately no separate `a2a.query` capability: both sides
publish/receive only `a2a.inbox`; a reply arrives as a task.

## How it works

Folder contract (the bridge adapter owns the tree):

```
<bridge_dir>/
├── registry/<bridge>.yaml   # manifest — the capability ships this
├── inbox/<bridge>/          # wrapper -> agent (adapter reads)
├── outbox/<bridge>/         # adapter -> wrapper (wrapper reads)
├── status/<bridge>/         # heartbeat / health of the bridge
└── media/<bridge>/{in,out}  # attachments
```

The capability's manifest ships `registry/<bridge>.yaml` into `<bridge_dir>`
— the adapter creates the folders; nothing else is manual.

Chain of an incoming task: the node's `a2a.inbox` handler **queues** the
payload into a wrapper feed (`requests/`); the **wrapper** is the single
writer of `inbox/a2a/` (it maps the request into the adapter's schema,
acks the request file, and later routes the reply out through the outbox).

Message schema (one JSON object per file in `inbox/<bridge>/`):

```
{
  "id": "a2a_<ts>_<rand>",
  "type": "message",
  "sender": "<iowap node id>",   // e.g. E4W3CBWQ, RYBFNMET — no label indirection
  "text": "<text>",
  "chat": {"id": "<agent-id>", "type": "direct", "name": "<agent-id>"},
  "attachments": [],
  "reply_to": "<id of the message this answers>"   // null for a fresh request
}
```

Reply path:

1. The receiving wrapper drains `outbox/<bridge>/*.json` (mtime-sorted,
   at-least-once with unlink-after-send).
2. Each drained reply is logged once to `sent.log` — the delivery proof.
3. `target` **is** the peer's iowap node id — the wrapper submits the task
   `<bridge>.inbox:{... reply_to ...}` with `--owner <node_id>` (no alias
   map, fail-closed: no regex match → no callback). On the peer, the task
   is claimed and the inbox file appears with `reply_to` set.

Loop protection: a message whose `reply_to` is set is a **reply**, not a
request — the receiving wrapper never echoes it back. That single guard is
enough; a reply never spawns another reply.

## Message types + routing (T-061E)

The `a2a.inbox` capability input schema (v1.3.0 on both ends) carries
`{text (required), from, reply_to, type}`. The optional `type` marker splits
traffic by what it needs from the receiver:

- `dialog` (absent or explicit) — an agent turn: the receiving wrapper writes
  the inbox file as before. A running series may bundle several dialogs into
  one turn (mode=a2a digest, below).
- `status` — run state only. The receiving wrapper appends the entry to its
  `status/<bridge>/liveness.json` ring (bounded to the last 100 entries) and
  acks the request: **no inbox file, no agent turn, no auto-reply/callback**.
  Agents publishing a progress stream (long running loops, self-reviews)
  SHOULD mark those messages `type: "status"` instead of letting them hit
  the peer's turn budget.
- `probe` — dropped with a log line, no state change.

`type` values outside the vocabulary are treated as `dialog`. A digest reply
is one task addressed back with `reply_to` set to the first id of the
coalesced series; it stands for the whole series.

Compute requests are **tasks, never chat**: call the peer's compute
capability directly via task submit (see [capabilities](capabilities.md))
instead of wrapping them into an a2a message.

### mode=a2a digest (bridge adapter)

Bridges serving A2A peer traffic can enable an adaptive digest in the
bridge adapter, deliberately outside unified threads (`mode=a2a`): the same
machinery pattern as the adaptive digest on unified threads, but with its
own state file (`a2a_digest_states.json`) and its own idle flush loop. The
first message of a quiet channel dispatches immediately; a message arriving
within the series gap (20 s) opens the digest window; buffered messages
flush as one bundled turn when the window elapses (25 s, idle timer) or the
burst cap (8 messages) is reached. Attachments and `/unified` commands
bypass the digest; `type: status`/`probe` messages never reach it (the
wrapper routes them before the inbox file exists). Post-flush cooldown
follows the T-080 semantics.

## What it is NOT

- No built-in chat UI and no conversation thread store — the relay routes
  capability strings, it does not interpret payloads.
- No per-message correlation in the relay core: `reply_to` lives in the
  payload, the wrapper carries it (prototype status).
- Not a replacement for `chat.ai` / `agent.ai` — those are client-to-agent
  calls; A2A is agent-to-agent.

## Related pages

- [capabilities](capabilities.md) — how `a2a.inbox` is advertised and matched
- [tasks](tasks.md) — the reply path is an ordinary task
- [artifacts](artifacts.md) — attachment transport (inline/artifact/bridge)
- **Bridge adapter:** [github.com/Kesuek/hermes-bridge-adapter](https://github.com/Kesuek/hermes-bridge-adapter) — the plugin that owns the `<bridge_dir>` file tree
- The bridge adapter is part of the **Hermes Plugin Catalog**:

  ```
  hermes plugins install bridge-adapter
  hermes plugins enable bridge-adapter
  ```