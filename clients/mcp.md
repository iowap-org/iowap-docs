# MCP toolkit for agents (iowap-client-mcp)

`iowap-client-mcp` ships an [MCP](https://modelcontextprotocol.io) stdio
server that gives any MCP-speaking AI agent (Hermes, OpenCode, …) a curated
IOWAP toolset — without the agent having to learn the node CLI's pitfalls.

The node CLI stays the source of truth for authentication and execution: the
server shells out to `node-cli --json` and adds **zero credential handling of
its own**. It runs as a plain MCP stdio subprocess spawned by the client
(daemon-free, no port, no service unit).

## Install

Requires an existing node installation on the same host
([node/setup](../node/setup.md)) so `node-cli` is available; the server
resolves the binary via the node's own pin
(`~/.relay/node.yaml` → `PATH` → known locations).

```bash
pip install "iowap-client-mcp[mcp]"
```

Live on the [Python Package Index](https://pypi.org/project/iowap-client-mcp/)
since 0.1.2 — or let a local node install it: `node-cli mcp install`
(own venv, client-neutral, PyPI registry — see [node CLI](../node/cli.md)
under `mcp`). Pinned alternatives live on the
[releases tab](https://github.com/iowap-org/iowap-client-mcp/releases) of
this repo's GitHub (wheel assets per release).

```console
$ iowap-mcp --version
0.1.2
```

## Wire an MCP client

Hermes Agent (`~/.hermes/config.yaml`):

```yaml
mcp_servers:
  iowap:
    command: "iowap-mcp"
```

Or `hermes mcp add iowap --command iowap-mcp`, then `/reload-mcp` (or a new
session) to pick the tools up. Any other MCP client uses the equivalent
stdio spawn (command `iowap-mcp`).

## Tools

| Tool | Answers |
|------|---------|
| `relay_status` | Relay health, queue depth, task counters (unauth probe — works while the local node daemon is down) |
| `node_list` | Fleet overview: node IDs, names, status, capabilities, load |
| `capabilities_list` | All capabilities with `input_schema` **and** the node IDs that own each one |
| `task_submit` | Submit a task (`payload` = the capability's schema; `owner_node_id` = a node ID, never a name; optional `name` labels the row); optional `wait_seconds` ≤ 90; auto-tracks the task on the desktop Tasks page (in-process, no extra bridge tool needed) |
| `task_result` | Task state + result (first completed stage, envelope-unwrapped) |
| `artifact_download` | Download a task artifact to an explicit local path (refuses to overwrite an existing file unless `overwrite: true`; file existence verified) |
| `docs` | The live documentation you are reading (list pages / read markdown) |

Typical loop: `capabilities_list` → pick capability + owning node ID →
`task_submit(capability, payload, owner_node_id, wait_seconds=60)` → read
`result`; poll `task_result` for long tasks.

## Updates

The toolkit is a regular PyPI package — a local node keeps it current for
free: `node-cli update check` reports the node wheel AND this toolkit;
`node-cli update apply` upgrades both (the toolkit in its own venv, no
service restart — a running `iowap-mcp` process reloads on the next client
spawn). Manual path: `pip install --upgrade iowap-client-mcp[mcp]`.
PyPI versions are immutable: every toolkit change ships as a version bump.

## Security boundary

- **Trust model:** whoever can launch `iowap-mcp` on the host acts with the
  node's identity — an MCP client that spawns this server is a trusted
  executor. Environment filtering of the stdio subprocess is host behavior
  (Hermes does it); the package relies on the node's on-disk identity and
  enforces none of it itself.
- **No destructive surface:** registration, wheel updates, capability
  publishing, daemon control, and token handling are deliberately not
  exposed. Those remain node-CLI operations for a human or a managed agent.
- **Narrowable execution:** operators can restrict which capabilities
  `task_submit` may fire with `IOWAP_ALLOW_CAPS=cap.one,cap.two` (csv env;
  unset means all published capabilities).
- **`artifact_download` writes a file:** it refuses to overwrite an existing
  path unless `overwrite: true` is passed.
- **Stdio only, by design:** the toolkit binds a **local** node to an AI agent
  on the same host. There is deliberately no remote/HTTP transport — exposing
  a node identity over the network is a leak path, not a feature. POSIX host
  (Linux/macOS) — no Windows support.

## Troubleshooting

- **No tools appear** in the client: check the client logs for spawn
  failures; `iowap-mcp` exits with an install hint when the `mcp` SDK is
  missing (`pip install "iowap_client_mcp[mcp]"` handles it).
- **`node-cli not found`:** the resolution chain walks the node's
  `node_cli_path` pin → `PATH` → known install locations; install
  [iowap-node](https://github.com/iowap-org/iowap-node) first.
- **`task_result` says `not_found`:** read scope is admin, the owner
  node, or the sender (`submitted_by` — the node that submitted the
  task). This node can always read back its own owner-directed
  results; `not_found` means a genuinely different identity submitted
  it (or the task is gone).