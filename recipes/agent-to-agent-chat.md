# Recipe: Agent-to-Agent Chat

> End state: two agents that talk to each other through the fabric — no
> chat server, no new protocol, no relay change. Reference deployment:
> `a2a.inbox` in production across three agents (a Hermes desktop node, a
> Mac build agent, and a flow orchestrator), including a three-way group
> conversation over the bridge adapter's unified threads.

## What you'll end up with

```text
Agent A                                Agent B
  │ task submit a2a.inbox:{from, text}  │
  │                                     │  handler → requests/<id>.json (wrapper feed)
  └────────────────────────────────────▶  wrapper → inbox/a2a/<id>.json
                                          agent B reads it, writes a reply
                                          outbox/a2a/<reply-id>.json
                                          wrapper send-hook:
                                            task submit a2a.inbox {reply_to} ──▶ Agent A
```

The full contract — message schema, identity hardening, loop protection,
digest behavior — is normative in
[a2a-bridge](../concepts/a2a-bridge.md). This recipe is the
**minimum setup** to get there.

## Ingredients

- Two registered nodes, each running an agent that can read files and
  write replies (this deployment uses Hermes agents; anything file-driven
  works)
- The [bridge-adapter](https://github.com/Kesuek/hermes-bridge-adapter)
  plugin on each agent's host:
  `hermes plugins install bridge-adapter && hermes plugins enable bridge-adapter`
- One capability declaration per node (~15 lines)

## Steps

### 1. Declare the inbox capability

The capability does exactly one thing: write the inbound message to a
folder. On each node's profile:

```yaml
- name: a2a.inbox
  version: 1.3.0
  claimable: true
  handler: /home/<user>/.relay/handlers/a2a-inbox-handler.py
  max_parallel: 4
  timeout: 30
  type: tool
  description: 'Agent-to-agent: writes the message into the bridge a2a
    inbox (dialog|status|probe). Parameter: text (required), from
    (informational), reply_to, type.'
  input_schema:
    fields:
      text:
        name: text
        type: string
        required: true
        description: 'The message body. Example: are you free for a review?'
      reply_to:
        name: reply_to
        type: string
        required: false
        description: 'Message id this answers. Null for a fresh request.'
      type:
        name: type
        type: string
        required: false
        description: 'dialog (default) | status | probe.'
```

### 2. Point the adapter at the folder tree

The capability's manifest ships `registry/<bridge>.yaml` into
`<bridge_dir>`; the adapter creates the rest of the tree on first message:

```text
<bridge_dir>/
├── registry/<bridge>.yaml   # manifest — ships with the capability
├── inbox/<bridge>/          # wrapper → agent (adapter reads)
├── outbox/<bridge>/         # adapter → wrapper (wrapper reads)
├── status/<bridge>/         # heartbeat / health
└── media/<bridge>/{in,out}  # attachments
```

### 3. Wire the agent loop

The agent side is ordinary file watching — in this deployment a small
wrapper script that feeds `inbox/a2a/*.json` to the agent session and
drains `outbox/a2a/*.json` back out (mtime-sorted, unlink-after-send).
Every drained reply becomes one task: `<bridge>.inbox:{…, reply_to}` with
`--owner <peer-node-id>`. `sent.log` is the delivery proof.

### 4. Probe — a real conversation

From agent A (via the fabric):

```console
$ iowap-cli task submit --name a2a-hello \
    --stage 'a2a.inbox:{"text":"ping — can you summarize repo state?","from":"<a-node-id>"}' \
    --owner <b-node-id>
```

Agent B's session shows the message, replies, and agent A receives a task
whose payload carries `reply_to` pointing at the original id. Two agents,
one conversation, zero relay changes.

## Variations

- **Three or more agents, one shared conversation:** the bridge adapter's
  *unified threads* mirror one agent's messages into the other members'
  inboxes — A2A2A without any new machinery. Group membership lives in the
  adapter, deliberately invisible to the relay.
- **Progress streams instead of chat turns:** mark machine-generated
  output `type: "status"` — the receiving side logs it to a bounded ring
  and consumes no agent turn.
- **Compute is not chat:** anything that needs a *result* (a file, a
  number, a verdict) is an ordinary task to the peer's capability —
  `paperless.search`, `model.specialist` — not an a2a message. A2A is for
  conversation; the task system is for work.

## Why this is one recipe and not a feature

Nothing above touched the relay: the chat lives in two wrapper processes
and a folder tree, addressed by a capability name the relay already
routes. That is the pattern this section wants to demonstrate — compose
the behavior you want from capabilities and adapters, and the fabric stays
dumb and reliable.
