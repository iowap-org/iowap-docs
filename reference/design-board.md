# Design Board — Historical Design Records

> **Historical design document.** The concepts on this page have either
> been implemented (see `concepts/*` for the current-state descriptions)
> or marked below as proposals. Nothing here describes the running
> system's current behavior — read [concepts](../concepts/overview.md)
> for that. Kept as design provenance for the decisions that shaped the
> system.

## Contents (historical)

1. **Message board concept** (node-to-node-to-human exchange, threaded
   conversations across agents, workers, and humans) — the board lives as
   db-node capabilities. Original design decisions:

   | Question | Decision |
   |---|---|
   | Separate db-node? | Yes — structured persistence, migrations, backups, search |
   | DB technology | SQLite + FTS5 for MVP; Postgres upgrade path |
   | Search location | Inside db-node (`db.search.query`); board-worker requests but does not own the index |
   | Per-board roles | Global dashboard roles for MVP |
   | AI replies | Opt-in per board (`allow_ai_replies`, default false) |
   | Deleted posts | Soft-delete (`deleted_at`); hard-delete reserved for admin purge |
   | System channel | No — relay events stay in SSE, not auto-posted |

2. **Design-time actor and data model diagrams** — superseded by the
   implemented models: [nodes](../concepts/nodes.md),
   [capabilities](../concepts/capabilities.md), [tasks](../concepts/tasks.md).

3. **MVP scope and prerequisite lists** (2025-era) — all items shipped.

## Where the real decisions live going forward

Project-level decisions and their reasoning are tracked in the boards'
`DECISIONS.md` (not in this repo). When a design reshapes behavior,
write the current state into `concepts/*` and record the reasoning on
the board — this file stays as historical record only.