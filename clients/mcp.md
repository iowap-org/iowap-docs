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
pip install "iowap_client_mcp[mcp] @ https://github.com/iowap-org/iowap-client-mcp/releases/download/wheel-v0.1.0/iowap_client_mcp-0.1.0-py3-none-any.whl"
```

The `mcp` extra pulls the MCP SDK (the toolkit itself has no runtime
dependencies). Verify:

```console
$ iowap-mcp --version
0.1.0
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
| `task_submit` | Submit a task (`payload` = the capability's schema; `owner_node_id` = a node ID, never a name); optional `wait_seconds` ≤ 90 |
| `task_result` | Task state + result (first completed stage, envelope-unwrapped) |
| `artifact_download` | Download a task artifact to an explicit local path (file existence verified) |
| `docs` | The live documentation you are reading (list pages / read markdown) |

Typical loop: `capabilities_list` → pick capability + owning node ID →
`task_submit(capability, payload, owner_node_id, wait_seconds=60)` → read
`result`; poll `task_result` for long tasks.

## Security boundary

- **No destructive surface:** registration, wheel updates, capability
  publishing, daemon control, and token handling are deliberately not
  exposed. Those remain node-CLI operations for a human or a managed agent.
- **Stdio only (v1):** tools run on the host that owns the node identity.
  A remote (HTTP transport) variant would require a dedicated service node
  identity — exposing the operator's node token to other machines is a leak
  path, not a feature.
- MCP hosts filter the subprocess environment by default; the toolkit reads
  relay credentials from the node's on-disk identity and needs neither
  `--env` secrets nor relay URLs in the client config.

## Troubleshooting

- **No tools appear** in the client: check the client logs for spawn
  failures; `iowap-mcp` exits with an install hint when the `mcp` SDK is
  missing (`pip install "iowap_client_mcp[mcp]"` handles it).
- **`node-cli not found`:** the resolution chain walks the node's
  `node_cli_path` pin → `PATH` → known install locations; install
  [iowap-node](https://github.com/iowap-org/iowap-node) first.
- **`task_result` says `not_found`:** for owner-directed tasks this is
  expected — only the owner node can read those results.