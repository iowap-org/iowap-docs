# Artifacts and File Transfer

This page answers: how do files travel between caller, relay, and
handler?

## What it is

The relay's artifact store (`~/.relay/artifacts/`) is a **transient
transfer buffer**, not an archive: it exists so medium-sized files can be
handed off between a caller and a handler without bloating the task payload
(base64 inline) or requiring a storage node. The payload carries a
reference (`artifact_id`); the handler downloads on demand. A watchdog
deletes every artifact older than `artifact_ttl_days` (default 7) —
regardless of whether the task still exists. The durable copy always lives
on the storage node.

The three modes form a deterministic size-based ladder:

| Rung | Mechanism | Bound |
|------|-----------|-------|
| 1. `inline` | base64 in the task payload | ≤ `max_inline_bytes` (default 5 MB) |
| 2. `artifact` | transient relay artifact store, payload carries `artifact_id` | ≤ `max_artifact_bytes` (default 50 MB) |
| 3. `bridge` | streamed through a temp route to a storage node, payload carries `storage_ref` | larger files, RAM-bounded, needs a storage node |

A capability's `upload_modes` field restricts which rungs it accepts; the
CLI primitives (`node-cli file send`/`file get`, `hp put`/`hp get`) pick
the smallest supported rung automatically — see
[capabilities](capabilities.md). The handler-side envelope format for
transferring files is the `__iowap_ref__` marker — normative in
[handler primitives](../node/handlers/primitives.md).

## How it works

1. The sender (CLI or handler) evaluates the ladder: capability modes ×
   server thresholds × file size → smallest fitting rung.
2. The chosen rung determines the payload carrier (`data_base64`,
   `artifact_id`, or `storage_ref` `{type, id, filename}`).
3. The receiving handler resolves the reference — downloads the artifact
   from the relay or streams from the storage node — and acknowledges.
4. The watchdog keeps the store bounded; nothing on the relay is durable.

## What it is NOT

- **Not an archive** — the store is transient by design (TTL cleanup);
  durable storage is a storage-node job.
- **Not node-to-node** — the relay (or a storage node) is always the
  intermediary; no direct node↔node transfer exists today (the ephemeral
  node-serve experiment was deliberately retired — its primitives live on
  as the `hp put/get` envelope helpers).
- **Not integrity-checked end-to-end by default** — the ladder carries a
  `sha256` where the envelope includes it; callers transferring critical
  files should include the checksum.

## Related pages

- [capabilities](capabilities.md) — `upload_modes` per capability
- [handler primitives](../node/handlers/primitives.md) — `hp put/get` reference
- [storage](../storage/storage.md) — the durable, bridge-side rung
- [glossary](glossary.md) — verbatim terminology