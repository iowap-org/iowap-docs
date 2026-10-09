# What is the Relay?

This page answers: what is the IOWAP relay, and what does it deliberately
not do?

## What it is

The relay is the **coordination layer** of an IOWAP cluster. It connects,
authenticates, and monitors a fleet of worker nodes, distributes tasks, and
publishes events. It never runs domain logic itself:

- It owns the node registry, heartbeat state, the task DAG, and the event
  stream.
- It routes work by **capability string**, matching stages to nodes. It does
  not choose tools, models, or parameters.
- Every domain service and every worker runs as an **external node** that
  registers over the public v2 API and advertises its own capabilities.

Because the core has no domain knowledge, it stays small, auditable, and
replaceable. All intelligence and all domain data live in the nodes.

```
                        ┌────────────────────────┐
                        │   IOWAP Relay          │
                        │   core — port 8788     │
                        │  Auth / Discovery /    │
                        │  Scheduler / Events    │
                        └────────────────────────┘
                                  ▲  ▲
         ┌────────────────────────┘  └────────────────────────────┐
         │ heartbeat / claim / complete           register        │
         ▼                                                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Node (one type, differentiated by capabilities)                     │
│                                                                      │
│  • chat.ai          → LLM chat          (worker on a Mac)           │
│  • image.gen.mflux  → image generation  (worker on a Mac)           │
│  • storage.archive  → archive files     (storage node on a NAS)     │
│  • federation       → bridge relays     (federation node)           │
└──────────────────────────────────────────────────────────────────────┘
```

One sentence: the relay answers **WHERE** a task can run, nodes answer
**HOW**, and the flow runner answers **WHAT** — no layer orchestrates the
others. Agents (such as the Hermes desktop integration) are clients of this
fabric, not its center.

## How it works

The relay exposes a versioned HTTP API under `/relay/v2` plus root-level
health endpoints (`/health`, `/ready`, `/metrics`). Nodes register, get
approved by an admin, and then heartbeat capabilities; the scheduler matches
pending stages to live providers by exact capability name; results flow back
as stage completions and typed SSE events.

The details live on their own pages:

- Node and heartbeat model: [nodes](nodes.md)
- Capability routing keys: [capabilities](capabilities.md)
- Task/stage lifecycle and statuses: [tasks](tasks.md)
- Credential families: [tokens](tokens.md)
- Security model: [security.md](security.md)

## What it is NOT

- **Not a task queue** — queue workers are centrally deployed and managed;
  IOWAP nodes advertise themselves from arbitrary devices.
- **Not an agent framework** — agent frameworks coordinate agents inside one
  runtime; IOWAP is the device fabric *under* agents. (A2A, MCP gateways,
  multi-agent frameworks, workflow tools — see below.)
- **Not the one who decides** — the core routes by capability string and
  cannot be tricked into running untrusted logic; it never interprets
  payloads.

### Neighboring approaches

IOWAP sits in a busy ecosystem — none of the things below, and the
differences are deliberate:

| Approach | What it does | How IOWAP differs |
|----------|--------------|-------------------|
| A2A (Agent2Agent) | Standard for agent↔agent communication (agent cards, task delegation) | IOWAP routes *between machines* using capability claims; agents are one client type. A2A could ride on IOWAP as an adapter node — not the other way round. |
| MCP gateways | Centralized tool / MCP-server distribution for agent processes | IOWAP operates *below* that layer: independent node daemons on real devices with heartbeat, load, and claim-based scheduling. An MCP gateway would run *as a node*. |
| Task queues (Celery, Asynq, taskiq) | Deployed, centrally configured workers | IOWAP nodes advertise themselves — no capability discovery, no heterogeneous device fleet in queues. |
| Multi-agent frameworks (Autogen, agent-framework, swarms) | Coordinate agents within a single runtime | IOWAP is the device fabric *under* the agents. |
| Workflow tools (n8n, Activepieces) | "Node" = graph step in one engine | IOWAP nodes are independently running machines; the flow runner composes *across* them. |

## Related pages

- [getting-started](../getting-started.md) — scenario-based introduction
- [server setup](../server/setup.md) — install and run the relay
- [API reference](../reference/api.md) — full endpoint table
- [glossary](glossary.md) — verbatim terminology used across the docs