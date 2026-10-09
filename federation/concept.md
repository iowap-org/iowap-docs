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
  end-to-end encryption — intermediate relays stay ahnungslos, in
  keeping with the system's pass-through principle.

Capability names imported from remote relays are namespaced
(e.g. `federation:<relay-name>:<capability>` style) so local routing
never collides with local capabilities. The return path (results flowing
back across federation) is the open design question — a pre-study exists
in the board's review findings.

Security-wise the two sides never share credentials: the federation node
holds one token per relay it belongs to, and fed-side links authenticate
with long-lived node keys (planned), not runtime tokens.

## What it is NOT (even once implemented)

- **Not a shared task queue** — a forwarded task is executed on the
  remote relay's normal scheduler; the origin relay only observes
  result state through the federation node.
- **Not automatic trust** — every remote capability import is an explicit
  subscription decision by the operator.
- **Not a relay-to-relay protocol** — federation runs through nodes on
  both sides; the relays themselves never talk to each other (keeps the
  relay ahnungslos by construction).

## Related pages

- [overview](../concepts/overview.md) — where federation sits in the landscape
- [capability model](../concepts/capabilities.md) — subscription/namespacing basis
- framework-internal APIs for implementing the node live in the
  iowap-federation repo (`docs/framework-ref.md`) — kept with the code