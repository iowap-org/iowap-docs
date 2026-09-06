# Handler Primitives (`node-cli hp put/get`, env-defaults, complete-by-script)

> T-179. This page documents the **extended handler contract** — everything
> here is opt-in. The default contract (stdin payload → stdout JSON result,
> daemon completes the stage) stays unchanged. See
> [capabilities.md](capabilities.md#handler-contract) for the default.

## Overview

Handler scripts get generic primitives from `node-cli` instead of building
transport logic themselves:

| Primitive | Command | What it does |
|---|---|---|
| **put** | `node-cli hp put <path> --cap <capability>` | Moves a local file into the task — prints a transfer *envelope* (JSON) to stdout |
| **get** | `node-cli hp get` | Reads an envelope (stdin or `--file`), downloads/decodes the file, prints its local path |
| **complete** | `node-cli complete <stage_id> --result-file <f>` | Completes a claimed stage; task/stage IDs default to env vars |
| **note** | `node-cli task note <task_id> <message>` | Appends a note to a task; task ID defaults to env var |

All primitives are subprocess calls (the decided integration form): the
CLI process loads the relay token (`RELAY_TOKEN_FILE`), does the HTTP
calls and picks the transport — **scripts never touch the token or
build HTTP themselves**.

## Envelope format (`__iowap_ref__`, v1)

An envelope is a JSON object with exactly one marker key; `hp put`
prints it on stdout, `hp get` consumes it:

```json
{"__iowap_ref__": {"v": 1, "src": "inline", "filename": "report.pdf",
 "size_bytes": 1234, "data_base64": "…", "sha256": "…"}}
```

| Field | Present for | Meaning |
|---|---|---|
| `v` | all | Envelope version (currently `1`) |
| `src` | all | Transfer rung: `inline` \| `artifact` \| `bridge` |
| `filename` | all | Original file name (informational, not trusted for paths) |
| `size_bytes` | all | Unencoded file size in bytes |
| `data_base64` | `inline` | File content, base64-encoded |
| `sha256` | all | Digest for verification on `hp get` (always present since T-166; `inline` computes it, `artifact`/`bridge` carry the sender's digest) |
| `artifact_id` | `artifact` | Reference into the relay's transient artifact store |
| `storage_ref` | `bridge` | Opaque storage reference (channel/backup id) |

Producers fail fast (`make_envelope` validates field combinations), so
a receiver only ever sees transport-caused errors. Unknown `v`/`src`
values break loudly instead of silently misresolving.

## `hp put` — the transfer ladder

```bash
envelope=$(node-cli hp put ./result.pdf --cap chat.ai)
# → {"__iowap_ref__": {...}}  (exactly one compact JSON line on stdout)
```

`hp put` picks the **smallest rung** the capability supports, using the
server ladder (`max_inline_bytes` / `max_artifact_bytes`) restricted by
the capability's `upload_modes` — the same decision logic as
`node-cli file send`:

1. `inline` if allowed and `size <= max_inline_bytes`
2. `artifact` if allowed and `size <= max_artifact_bytes`
3. else: error `file too big: … (server ladder: inline<=…, artifact<=…)`

MVP limit on the producing side: ~~`bridge` envelopes can be *represented*
in the format, but `hp put` cannot build one yet~~ — **obsolete since
T-166**: `hp put` builds `bridge` envelopes via the ephemeral node serve
(see [bridge rung](#bridge-rung-ephemeral-node-serve-t-166) below).

Exit codes: `0` ok, `1` server/decision error, `2` usage (file missing).

`hp get` resolves `inline`, `artifact` **and** `bridge` (T-166).

## bridge rung (ephemeral node serve, T-166)

The `bridge` rung skips server-side storage entirely: the file is
served **from the sending node's daemon** and dies after the transfer.

**Producer (`hp put`, mode `bridge`):**

1. Discovers the daemon's serve endpoint via `~/.relay/serve.json`
   (written by the node daemon at startup) and probes it. Unreachable →
   `hp put: ephemeral serve not reachable (is the node daemon running?) —
   use artifact fallback`, exit `1`.
2. Stages the file to `~/.relay/serve/<transfer_id>` (22-char
   `secrets.token_urlsafe(16)` id), `max_downloads=1` by default.
3. Registers a temporary route `POST /download/<transfer_id>` (TTL
   3600 s) on the relay, pointing at the local serve endpoint.
   Registration failure → staged file removed, exit `1`.

**Consumer (`hp get`, `storage_ref = {"type": "node_serve", "node_id",
"path", "expires_at"}`):** pulls `{base_url}/relay/v2/dashboard/api/
node-routes/<node_id><path>` via **POST with empty body** + Bearer
token, streams to disk, verifies `sha256`. The consumer **never
unregisters** — Ephemeralität is the sender daemon's job (F6/F7).

**Ephemeralität:** after the Nth successful download (default 1) the
daemon deletes file + manifest and unregisters the relay route; a
second `hp get` fails with a transport error (relay 404). A TTL sweep
is the backstop for never-pulled transfers (default TTL 3600 s).
Set `IOWAP_SERVE_COUNT` (1–10) to allow N downloads instead of 1.

**Requirements:** the sending node's daemon must run (it hosts the
serve thread, env `IOWAP_SERVE_PORT`; bind failure degrades to a
warning — `hp put` then reports the unreachable serve).

**Bind/advertise host (D8):** the serve binds and advertises via
`serve_host()`: env `IOWAP_SERVE_HOST`, default `127.0.0.1`
(single-host deployments: relay dials the node on the same machine —
plan behaviour). For relay-on-LXC / node-on-LAN deployments set
`IOWAP_SERVE_HOST` to the node's LAN IP so the relay proxy can reach
the serve (`0.0.0.0` works for the bind; the manifest advertises the
same value). Invalid values fall back to the default with a warning.

**Source-IP allowlist (D9):** whenever the serve is reachable beyond
loopback, every request's **socket peer** (`X-Forwarded-For` is never
trusted) is checked against an allowlist resolved once at bind time:
the relay's IP (env `IOWAP_SERVE_ALLOW` override, else resolved from
the node's relay config base URL), the advertise host's IP (the local
CLI probes the advertise address), and loopback. Everything else gets
`403 {"error":"forbidden"}` — fail-closed: if the relay IP cannot be
resolved, remote peers are rejected (warning at bind; set
`IOWAP_SERVE_ALLOW` and restart the daemon). Single-host deployments
(loopback bind only) are unaffected.

## `hp get` — resolve an envelope

```bash
node-cli hp get <<< "$envelope"
# → {"path":"/home/felix/.relay/tmp/<task_id>/report.pdf","size_bytes":1234,"src":"inline"}
```

- Reads the envelope from **stdin** or `--file <path>`; invalid JSON or
  a missing `__iowap_ref__` key → usage error (exit `2`).
- Writes the file to `~/.relay/tmp/<task_id>/` (task id from
  `RELAY_TASK_ID`; `adhoc` outside a handler) or to `--output <path>`.
- Verifies the `sha256` if the envelope carries one; mismatch → error,
  partial file removed (exit `1`).
- The envelope's `filename` is sanitized (`Path(...).name`, no
  directory traversal) before it is used as the default file name.

## Env-defaults for complete/note

`handler_runner` exports `RELAY_TASK_ID`, `RELAY_STAGE_ID`,
`RELAY_CAPABILITY`, `RELAY_NODE_ID`, `RELAY_BASE_URL`,
`RELAY_TOKEN_FILE` to every handler. The completion/note primitives
pick their IDs from these when flags are omitted — explicit flags win:

```bash
# inside a handler script (RELAY_* already set):
node-cli complete --result-file ./result.json      # stage = RELAY_STAGE_ID, task = RELAY_TASK_ID
node-cli task note "processed 3 files"             # task = RELAY_TASK_ID
```

Without any ID (and outside a handler) both commands print a stderr
message and exit `1`.

## `complete_by_script` (opt-in per capability)

```yaml
capabilities:
  - name: chat.ai
    config:
      complete_by_script: true
```

- **Default contract stays the default.** Without the flag nothing
  changes: the daemon parses stdout and completes the stage.
- With the flag, the handler script completes its own stage (`node-cli
  complete …`) and leaves stdout empty. The daemon still attempts its
  fallback complete; the relay's *"already completed"* 404
  (`not claimed by this node, or not in claimed status`) is counted as
  **success**, not failure.
- Rationale: a script-side complete avoids the claim-TTL race where a
  long-running handler's result gets discarded after the TTL expires.

## Security convention

- `put`/`get` are pure data operations — no task/stage scoping applies.
- `complete`/`note` are conventionally scoped to the **own**
  task/stage (env vars); client-side first. Server-side scoped tokens
  are a follow-up on the iowap-server side (out of scope here).
- The token stays inside the CLI process (`RELAY_TOKEN_FILE` →
  RelayClient); scripts never read it.