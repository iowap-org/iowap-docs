# CLI Reference — `node-cli`

Every command, verified against the argparse tree in
`nodes/common/node_cli.py` (iowap-node). Per-flag details:
`node-cli <command> <action> --help` is the complete source of truth —
this page documents structure, defaults, and behaviour.

## Global flags

| Flag | Meaning |
|------|---------|
| `--json` | Raw JSON output instead of formatted text — for scripting and automation. Supported by most data commands. |
| `--log-level` | `DEBUG`/`INFO`/`WARNING`/`ERROR` (default: env `RELAY_LOG_LEVEL` or `INFO`) |

## Command tree

| Command | Action | Purpose |
|---------|--------|---------|
| `daemon` | `start · stop · status · restart · foreground` | Control the background daemon (polling variant) |
| `node-daemon` | *(own console script)* | SSE-driven daemon — see [operations](operations.md) |
| `heartbeat` | — | Send a single heartbeat and exit |
| `claim` | `--capability <cap>` | Claim one stage for a capability |
| `complete` | `[stage_id] --result-file <f>` | Complete a claimed stage (IDs default to `RELAY_*` env) |
| `task` | `submit · result · wait · note` | Submit (`--stage <cap>:<json>`, `--priority 0-10`, `--owner <node_id>`, `--name`), show result, wait (`--interval`, default 5 s), append note (1–2000 chars) |
| `capabilities` | `list · validate · publish · diff · current · server · info` | Profile management — validate/publish atomically; `server`/`info` read the relay's registry |
| `node` | `list · info · busy · idle · clear-status · status · register` | Fleet queries + own status + self-registration |
| `server` | `health · metrics` | Unauthenticated probes of a relay (health + ready / Prometheus gauges) |
| `relay` | `set · discover` | Pin the relay URL (`--server-url` / `--discover`) or mDNS lookup (`discover --timeout`) |
| `route` | `register · unregister · list` | Temporary bridge routes (TTL'd, `--channel`, `--ttl`) |
| `bridge` | `upload · download` | Large files via the storage-node channel flow |
| `file` | `send · get` | Generic transfer ladder (inline/artifact/bridge, auto-chosen; `--force` override) |
| `hp` | `put · get` | Handler primitives — wrap/resolve `__iowap_ref__` envelopes ([reference](handlers/primitives.md)) |
| `artifact` | `upload · download` | Relay artifact store (`artifact upload <file> --name`, `download <id> --output`) |
| `docs` | `[<name>]` | Read relay documentation — no arg lists the index, a name prints the page as text |
| `status` | — | Print `worker_status.json` content |
| `reload` | — | Send SIGHUP to the running daemon (profile reload) |
| `update` | `check · apply` | Wheel-based self-update against GitHub releases — `check` compares versions, `apply` installs + restarts the service |

## Key behaviours

**Exit codes:** `0` success · `1` server/API/decision error · `2` usage
error (missing file, invalid arguments).

**Registration:** `node-cli node register <host[:port]|url>` creates state
files itself and writes nothing on failure; re-registering a live identity
needs `--force` (409 otherwise).

**Auth:** every authenticated command reads
`~/.relay/iowap-agent.token`. On 401/403 the client reloads the file and
retries refresh/recovery, then backs off exponentially (10→160 s, cap
300 s) — see [operations](operations.md).

**Task submission:** `node-cli task submit --capability <cap> --payload '
<json>'` is the old spelling; current form is
`task submit --stage "<capability>:<json>"` with optional
`--priority`/`--owner`. Stage payload fields must match the capability's
`input_schema` (see [capabilities how-to](capabilities.md)).

**`task wait`** polls until the task is terminal and prints the result —
the scriptable building block for submit→wait workflows.

**`docs`:** flat slugs (e.g. `node-cli docs node-setup`, `docs
reference-api`) — the index shape and slug stability are a compatibility
contract; list without argument shows every served page.

**`update`:** self-update for the node **and** the installed MCP toolkit.
Source: **PyPI by default** (`--source auto` = PyPI JSON API, falling back
to the GitHub `wheel-vX.Y.Z` release when PyPI is unreachable; `--source
pypi`/`--source github` pin strictly). `update check` reports both wheels
(node + `iowap-client-mcp` when present); `update apply` upgrades them
(the toolkit in **its own venv**, discovered via the `iowap-mcp` binary —
PATH, `~/.local/bin`, well-known venv layouts, or the Hermes MCP
registration — a running MCP server reloads on the next client spawn, no
restart needed) and restarts the node daemon after the wheel changed.
Two honesty guarantees: the updater refuses editable installs
(`dir_info.editable` in `direct_url.json` — local-wheel installs stay
updatable), and when pip resolves nothing despite a newer PyPI JSON (its
simple index can lag PyPI's edge, TTL minutes) the result is a retriable
failure, never a lying success. `apply` with nothing to update is a clean
no-op success (rc 0).

**`mcp`** (`node-cli mcp install` / `node-cli mcp status`): installs and
verifies the MCP toolkit (`iowap-client-mcp`) into its own venv from PyPI
(default `~/iowap-client-mcp/.venv`, `--venv`/`IOWAP_MCP_VENV` to place it)
and reports the stdio command path as data — `status` shows discovery +
installed/PyPI versions read-only. Client-neutral by design: no wiring
into any MCP client happens here (Hermes, Codex, … register the command
path themselves). The toolkit stays visible to `update check/apply` via
the same discovery chain.

## Verification

```bash
node-cli status
# -> worker_status.json content (status, auth state, last heartbeat)

node-cli server health --json
# -> {"health": {...}, "ready": {...}} — no credentials needed
```

## Related pages

- [setup](setup.md) — install, register, first daemon
- [operations](operations.md) — daemon variants, maintenance, backoff
- [capabilities how-to](capabilities.md) — profiles behind `capabilities` commands
- [handler primitives](handlers/primitives.md) — the `hp` commands in depth
- [storage bridge](../storage/storage.md) — `bridge upload/download` flow