# Handler Primitives — `hp put/get`, complete-by-script

> Everything on this page is **opt-in**; the default contract (stdin
> payload → stdout JSON result, daemon completes the stage) is unchanged —
> normative reference: [handler contract](contract.md).

Two kinds of "envelope" — don't confuse them: the **transfer envelope**
documented here (`__iowap_ref__`, moves files into/out of tasks) and the
**handler result envelope** (`{"status", "result", "error"}`, the I/O of
every invocation). A handler can use both independently: emit the result
envelope on stdout and, inside its `result`, carry a transfer envelope
produced by `hp put`.

## Overview

Handler scripts get generic primitives from `node-cli` instead of building
transport logic themselves. All primitives are subprocess calls: the CLI
loads the relay token (`RELAY_TOKEN_FILE`), makes the HTTP calls, and picks
the transport — **scripts never touch the token or HTTP themselves**.

| Primitive | Command | What it does |
|---|---|---|
| **put** | `node-cli hp put <path> --cap <capability>` | Moves a local file into the task — prints a transfer envelope to stdout |
| **get** | `node-cli hp get` | Reads an envelope (stdin or `--file`), resolves the file, prints its local path |
| **complete** | `node-cli complete --result-file <f>` | Completes a claimed stage; IDs default to env vars |
| **note** | `node-cli task note "<message>"` | Appends a task note; task ID defaults to the env var |

## Transfer envelope format (`__iowap_ref__`, v1)

A JSON object with exactly one marker key — `hp put` prints it, `hp get`
consumes it:

```json
{"__iowap_ref__": {"v": 1, "src": "inline", "filename": "report.pdf",
 "size_bytes": 1234, "data_base64": "…", "sha256": "…"}}
```

| Field | Present for | Meaning |
|---|---|---|
| `v` | all | Envelope version (currently `1`) |
| `src` | all | Transfer rung: `inline` \| `artifact` \| `bridge` |
| `filename` | all | Original name (informational — sanitized on use, not trusted) |
| `size_bytes` | all | Unencoded file size |
| `data_base64` | `inline` | File content |
| `sha256` | all | Digest, verified on `hp get` |
| `artifact_id` | `artifact` | Reference into the relay's transient artifact store |
| `storage_ref` | `bridge` | Storage reference (channel/backup id on a storage node) |

Producers fail fast (field combinations are validated at construction);
unknown `v`/`src` values error loudly instead of silently misresolving.

## Ladder — `hp put` picks the smallest rung

```bash
envelope=$(node-cli hp put ./result.pdf --cap storage.store.native)
# -> {"__iowap_ref__": {...}}   (exactly one compact JSON line on stdout)
```

Decision logic (shared with `node-cli file send`): `inline` if allowed
and ≤ `max_inline_bytes`, else `artifact` if allowed and ≤
`max_artifact_bytes`, else `bridge` if the capability allows it, else the
error `file too big: … (server ladder: inline<=…, artifact<=…)`.
`--force` overrides but must be in the capability's `upload_modes`.
Exit codes: `0` ok, `1` server/decision error, `2` usage (file missing).

The `bridge` rung historically used the node's ephemeral file-serve
(direct node↔node) — that mechanism is **retired** (project decision,
October 2026); bridge transfers stream through the **storage node**
channel flow instead. Capabilities declaring `bridge` need a live storage
node with `storage.upload_channel`/`storage.download_channel` — see
[storage](../../storage/storage.md).

## Resolving — `hp get`

```bash
node-cli hp get <<< "$envelope"
# -> {"path":"~/.relay/tmp/<task_id>/report.pdf","size_bytes":1234,"src":"inline"}
```

- Reads the envelope from **stdin** or `--file <path>`; invalid JSON or
  missing marker → usage error (exit `2`).
- Writes to `~/.relay/tmp/<task_id>/` (task id from `RELAY_TASK_ID`;
  `adhoc` outside a handler) or `--output <path>`.
- Verifies `sha256` when present; mismatch → error, partial file removed
  (exit `1`).

## Env-defaults for complete/note

Every handler receives (`handler_runner`):

| Variable | Content |
|---|---|
| `RELAY_TASK_ID` / `RELAY_STAGE_ID` | Claim identity |
| `RELAY_CAPABILITY` / `RELAY_NODE_ID` | Being executed / who |
| `RELAY_BASE_URL` / `RELAY_TOKEN_FILE` | Relay connection + token path |

The completion/note primitives take IDs from these when flags are omitted
(explicit flags win):

```bash
# inside a handler script (RELAY_* already set):
node-cli complete --result-file ./result.json
# -> stage = RELAY_STAGE_ID, task = RELAY_TASK_ID
node-cli task note "processed 3 files"
# -> note appended to RELAY_TASK_ID
```

Without IDs (and outside a handler) both print a stderr message and exit
`1`.

## `complete_by_script` (per capability)

```yaml
capabilities:
  - name: chat.ai
    config:
      complete_by_script: true
```

With the flag the handler completes its own stage (`node-cli complete …`)
and leaves stdout empty; the daemon's fallback complete meets the relay's
*"already completed"* 404 and counts it as success. Without the flag the
default contract applies unchanged. **Rationale:** avoids the claim-TTL
race where a long-running handler's result gets discarded after the TTL
expires — the script pins the result while its lease is alive.

## Security convention

- `put`/`get` are pure data operations — no task/stage scoping applies.
- `complete`/`note` are scoped to the **own** task/stage via the env vars
  (client-side convention; server-side token scoping is a follow-up).
- The token stays inside the CLI process (`RELAY_TOKEN_FILE` →
  RelayClient); scripts never read it.

## Related pages

- [handler contract](contract.md) — the default I/O envelope
- [capabilities how-to](../capabilities.md) — profiles, upload_modes
- [artifacts](../../concepts/artifacts.md) — the ladder concept
- [storage](../../storage/storage.md) — the bridge rung's storage node