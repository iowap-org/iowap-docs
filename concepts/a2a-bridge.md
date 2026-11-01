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