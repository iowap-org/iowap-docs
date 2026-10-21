# Federation

> **Status:** V1 forward path implemented; result return leg open.
> *(Canonical status string — use it verbatim in every repo's README and
> status block; the detailed table lives in the iowap-federation repo.)*
> The federation node's V1 forward path (Inbox/Outbox, transport
> abstraction, task export) ships in
> [iowap-org/iowap-federation](https://github.com/iowap-org/iowap-federation)
> (implementation notes + status table: its `docs/federation.md`).
> The result return leg is open design work. Framework-internal APIs for
> developing against the node framework: its `docs/framework-ref.md`.

## What it is

A **Federation Node** bridges capabilities between two or more relays.
It is not a special node type — it is a normal node heartbeating the
`federation` capability. When connected to a remote relay it imports
remote capabilities and offers them locally, or exports local
capabilities to the remote relay.

The node has two strictly separated sides:

- **Relay-side (inward)** — behaves exactly like a normal node: heartbeats,
  claims, completes. Exposes only the imported remote capabilities; the
  local relay sees just another node and learns none of the federation
  internals.
- **Fed-side (outward)** — an encrypted channel to other federation nodes;
  forwards tasks to them or receives tasks from them. Transport-agnostic
  by design (candidate transports: HTTP, store-and-forward over email,
  peer-to-peer); task payloads cross as message envelopes with
  end-to-end encryption — intermediate relays stay clueless, in
  keeping with the system's pass-through principle.

Capability names imported from remote relays are namespaced
(e.g. `federation:<relay-name>:<capability>` style) so local routing
never collides with local capabilities. The return path (results flowing
back across federation) is the open design question — a pre-study exists
in the board's review findings.

Security-wise the two sides never share credentials: the federation node
holds one token per relay it belongs to, and fed-side links authenticate
with long-lived node keys (planned), not runtime tokens.

## The node tail and the worker part

Every node is the same two-part construct. The split matters because the
**tail is identical across all node types** and the **worker part is what
makes a node specific**:

- **Node tail** — the part every node has: the heartbeat to its relay, the
  credential handling, task in and task out. Same shape for a storage node,
  a flow node, a home-assistant node or a federation node.
- **Worker part** — what actually performs work: the scripts it runs, the
  interfaces it talks to. This is what differs per node type. The
  home-assistant node is a particularly elaborate example of a worker part:
  it speaks to a supervisor API, manages services, and carries a domain
  model of its own.

A federation node is not a new node type in this sense: its tail is the
standard node tail, and its worker part additionally carries the fed-side
channel. That is why federation is described as "a normal node that also
bridges" — the tail grows no federation special case.

**Why it matters:** the tail is what the relay sees, so the tail is what
the heartbeat reports. The worker part is what the operator configures
locally. A configuration change only needs to be reported to the server
when it changes something the **relay** must know about — the worker part
never does. A federation node extends only the tail's reporting, with the
federation-specific view: which recipients it can address, which of its
own capabilities are exposed to federation, and which remote capabilities
it wants to import.

## Transports are channels, not partners

A federation node knows no remote relay endpoints. It knows the
**registered transports** — e-mail, a messaging service, a shared folder —
and addresses a recipient on one of them:

```
email~ronny.pietschke@icloud.com
nextcloud~peter
```

A transport is registered by dropping a manifest into the federation root;
the presence of the file means registered, removing it means unregistered.
The per-transport directories (inbox, outbox, status, media) appear
automatically on registration.

The outbox file **is** the message to the recipient. The task travels as an
attachment inside an encrypted file, so the transport never needs to
understand the payload and never holds a key. Each transport declares its
own limits — e-mail attachments are far smaller than a shared folder — and
the node must know that limit *before* routing, otherwise it routes a task
the transport structurally cannot accept. A task that exceeds the limit is
a terminal condition, not a retryable one.

**The consequence:** encryption belongs to the message, not to the
transport. A transport moves opaque bytes. This is what lets any
asynchronous transport work without re-implementing crypto per transport.

## Grants: three decisions, three owners

The topology is strictly `Server A ↔ FedNode A ↔ FedNode B ↔ Server B`.
There is **no server-to-server communication** — each server talks only to
its own federation node. That keeps the relay clueless by construction and
makes federation a **two-sided consent** without a central arbiter.

```
NovaForge A        FedNode A        Server A        FedNode B        Server B
     │                  │                │               │                │
     │ image.mflux      │ "I offer this, │               │                │
     │ released for fed │  I know        │               │                │
     ├─────────────────►│  cluster B"    │               │                │
     │                  ├───────────────►│               │                │
     │                  │                │ admin grants │                │
     │                  │                │ image.mflux  │                │
     │                  │                │ → cluster B, │                │
     │                  │                │ 1 task/hour  │                │
     │                  │◄───────────────┤               │                │
     │                  │ "what is       │               │                │
     │                  │  released, for │               │                │
     │                  │  whom?"        │               │                │
     │                  ├──────────────────────────────►│                │
     │                  │                │               │ "image.mflux?" │
     │                  │                │               ├───────────────►│
     │                  │                │               │                │ admin B
     │                  │                │               │                │ subscribes
     │                  │                │               │◄───────────────┤
```

Three decisions, three owners — the effective rule is their intersection:

| Decision | Owner | Means |
|---|---|---|
| **Expose** | node operator (A) | which local capabilities may leave via federation |
| **Grant** | server operator (A) | which remote side may use them, and with what limits |
| **Subscribe** | node operator (B) | which remote capabilities to import |

This is the same split the [forward routing](../concepts/forward-routing.md)
feature already uses: the node declares, the server assigns, the node
enforces. The declaration is node-owned, the assignment is admin-owned, the
enforcement is node-owned.

**Enforcement follows visibility.** The server does not see the tasks, so
it can only *declare* a limit — the federation node enforces it. Limits
therefore belong to the granting relationship, not to the capability in
isolation: "one task per hour" is a statement about a capability *towards a
particular peer*, and the peer is part of the grant.

**A limit is a budget, not a slot.** With asynchronous transports a task
can run for minutes; a "max one at a time" rule would let a single long
task block the channel. "One task per hour" therefore means *one start per
hour*, regardless of how long the task then runs.

## What it is NOT (even once implemented)

- **Not a shared task queue** — a forwarded task is executed on the
  remote relay's normal scheduler; the origin relay only observes
  result state through the federation node.
- **Not automatic trust** — every remote capability import is an explicit
  subscription decision by the operator.
- **Not a relay-to-relay protocol** — federation runs through nodes on
  both sides; the relays themselves never talk to each other (keeps the
  relay clueless by construction).
- **Not a transport-aware node** — a transport is a file channel with no
  knowledge of the payload. The node addresses `<transport>~<recipient>`;
  the transport sees opaque bytes.

## Related pages

- [overview](../concepts/overview.md) — where federation sits in the landscape
- [capability model](../concepts/capabilities.md) — subscription/namespacing basis
- [forward routing](../concepts/forward-routing.md) — the declare/assign/enforce
  split that grants mirror
- [nodes](../concepts/nodes.md) — node model, heartbeat, node tail
- framework-internal APIs for implementing the node live in the
  iowap-federation repo (`docs/framework-ref.md`) — kept with the code
