## CLI Reference (node-cli)

Every command, subcommand, flag and its help of the **node** CLI — generated **from the live argparse tree** (the parser is the contract): this page matches the executable that ships from the same tree. Narrative flows live in [node/cli](../node/cli.md); the relay's HTTP surface in [api](api.md).

### Global flags

| Flag | Meaning |
|---|---|
| `--json` | machine-readable single-line JSON for every command |
| `--log-level` | verbosity of the human output |

### Commands

| Command | Purpose |
|---|---|
| `daemon` | Control the background daemon. |
| `heartbeat` | Send a single heartbeat and exit. |
| `claim` | Claim one stage for a capability. |
| `complete` | Complete a claimed stage. |
| `task` | Task operations. |
| `capabilities` | Capability profile management. |
| `node` | Node operations (list, info, busy/idle/status). |
| `server` | Inspect a relay server (health, metrics) without node credentials. |
| `relay` | Relay connection management (pin URL or discover via mDNS). |
| `route` | Manage temporary bridge routes (T-136). |
| `bridge` | Upload/download large files via a temp bridge route (T-129/T-153). |
| `file` | Send/get files via the generic transfer ladder (T-164). |
| `hp` | Handler primitives for handler scripts (T-179). |
| `status` | Print worker_status.json content. |
| `reload` | Send SIGHUP to running daemon. |
| `artifact` | Artifact operations. |
| `docs` | Read relay documentation from the server (list all, or print one). |
| `update` | Check for and apply self-updates (PyPI-first, GitHub fallback). |
| `mcp` | Manage the local MCP toolkit (iowap-client-mcp). |

### `daemon`

Control the background daemon.

#### `daemon start`

*(no additional arguments — global flags apply)*

#### `daemon stop`

*(no additional arguments — global flags apply)*

#### `daemon restart`

*(no additional arguments — global flags apply)*

#### `daemon foreground`

*(no additional arguments — global flags apply)*

#### `daemon status`

show daemon status

*(no additional arguments — global flags apply)*

### `heartbeat`

Send a single heartbeat and exit.

*(no additional arguments — global flags apply)*

### `claim`

Claim one stage for a capability.

| Argument/Flag | Meaning |
|---|---|
| ``capability`` | Capability name to claim. *(positional)* |

### `complete`

Complete a claimed stage.

| Argument/Flag | Meaning |
|---|---|
| ``stage_id`` | Stage ID to complete. *(positional)* |
| `--task` | Task ID of the stage (default: RELAY_TASK_ID env, T-179). |
| `--result-file` | Path to a JSON file containing the result dict. |

### `task`

Task operations.

#### `task submit`

Submit a single-stage task.

| Argument/Flag | Meaning |
|---|---|
| `--name` | Task name (default: auto). |
| `--stage` | Stage as <capability>:<json-payload>. |
| `--priority` | Task priority 0-10. |
| `--owner` | Node ID that must claim this task (owner_node_id). |
| `--forward-slot <slot>` | Submit against the relay's 'forward' pseudo-capability: replaces the --stage capability with 'forward' and carries the slot in the payload; the relay resolves (this node, slot) -> target capability via its forward mappings (slots are per-node, 1..64 chars of A-Za-z0-9_-). |

#### `task result`

Show task result (status, stages, artifacts).

| Argument/Flag | Meaning |
|---|---|
| ``task_id`` | Task ID to query. *(positional)* |

#### `task wait`

Wait for a task to complete and show result.

| Argument/Flag | Meaning |
|---|---|
| ``task_id`` | Task ID to wait for. *(positional)* |
| `--interval` | Poll interval in seconds (default: 5). |

#### `task note`

Append a free-form note to a task (T-052 mini-chat).

| Argument/Flag | Meaning |
|---|---|
| ``task_id`` | Task ID to add a note to. *(positional)* |
| ``message`` | Note text (1..2000 characters). *(positional)* |

### `capabilities`

Capability profile management.

#### `capabilities list`

List profiles in profiles.d/.

*(no additional arguments — global flags apply)*

#### `capabilities validate`

Validate a profile (default: active).

| Argument/Flag | Meaning |
|---|---|
| ``profile`` | Profile name (default: active). *(positional)* |

#### `capabilities publish`

Validate + atomically copy profile to active.

| Argument/Flag | Meaning |
|---|---|
| ``profile`` | Profile name to publish. *(positional)* |

#### `capabilities diff`

Diff working profile vs active.

| Argument/Flag | Meaning |
|---|---|
| ``profile`` | Profile name (default: active). *(positional)* |

#### `capabilities current`

Show active profile name.

*(no additional arguments — global flags apply)*

#### `capabilities server`

Query capabilities registered on the relay server (all nodes).

*(no additional arguments — global flags apply)*

#### `capabilities info`

Show detailed info for a single capability registered on the relay.

| Argument/Flag | Meaning |
|---|---|
| ``name`` | Capability name to query. *(positional)* |

### `node`

Node operations (list, info, busy/idle/status).

#### `node list`

List all nodes registered on the relay server.

*(no additional arguments — global flags apply)*

#### `node info`

Show detailed info for a single node.

| Argument/Flag | Meaning |
|---|---|
| ``node_id`` | Node ID to query. *(positional)* |

#### `node busy`

Mark this node as busy (stops it from claiming new stages).

| Argument/Flag | Meaning |
|---|---|
| `--once` | Send a single heartbeat carrying the new status immediately. |

#### `node idle`

Mark this node as idle (available for claiming stages again).

| Argument/Flag | Meaning |
|---|---|
| `--once` | Send a single heartbeat carrying the new status immediately. |

#### `node clear-status`

Remove an explicit busy/idle request and restore automatic status handling.

| Argument/Flag | Meaning |
|---|---|
| `--once` | Send a single heartbeat after clearing the requested status. |

#### `node status`

Show the local + server-side node status.

*(no additional arguments — global flags apply)*

#### `node register`

Register this node on a relay server (creates local state files).

| Argument/Flag | Meaning |
|---|---|
| ``server`` | Relay server: IP/host, IP:port, or full URL (default port 8788). *(positional)* |
| `--name` | Node name (default: hostname). |
| `--force` | Re-register even if local node state already exists. |
| `--timeout` | HTTP timeout for the registration request (default: 15s). |

### `server`

Inspect a relay server (health, metrics) without node credentials.

#### `server health`

One-shot health probe (/health + /ready).

| Argument/Flag | Meaning |
|---|---|
| ``server`` | Relay server: IP/host, IP:port, or full URL (default port 8788). *(positional)* |

#### `server metrics`

Show Prometheus metrics (gauges) from the relay server.

| Argument/Flag | Meaning |
|---|---|
| ``server`` | Relay server: IP/host, IP:port, or full URL (default port 8788). *(positional)* |

### `relay`

Relay connection management (pin URL or discover via mDNS).

#### `relay set`

Pin the relay base_url, or remove the pin (--discover).

| Argument/Flag | Meaning |
|---|---|
| `--server-url` | Pin this relay URL (discovery disabled). |
| `--discover` | Remove the pinned URL and re-enable mDNS discovery. |

#### `relay discover`

Targeted mDNS lookup for the relay service name.

| Argument/Flag | Meaning |
|---|---|
| `--name` | Expected service name (default: mdns_service_name from relay_config.json, then 'IOWAP Relay Service'). |
| `--timeout` | Seconds to watch the network (default 2.0). |

### `route`

Manage temporary bridge routes (T-136).

#### `route register`

Register a temporary bridge route.

| Argument/Flag | Meaning |
|---|---|
| `--path` | Route path (e.g. /upload/abc123). |
| `--method` | HTTP method (GET/POST/PUT/...). |
| `--upstream` | Upstream URL the relay proxies to. |
| `--ttl` | Time-to-live in seconds. |
| `--channel` | channel_id tying this route to a session. |
| `--description` | Optional human-readable note. |

#### `route unregister`

Revoke a temp route before its TTL.

| Argument/Flag | Meaning |
|---|---|
| `--path` | Route path to delete. |
| `--method` | HTTP method of the route. |

#### `route list`

List this node's own routes (temp + permanent).

*(no additional arguments — global flags apply)*

### `bridge`

Upload/download large files via a temp bridge route (T-129/T-153).

#### `bridge upload`

Open a bridge channel and stream a local file TO the storage node.

| Argument/Flag | Meaning |
|---|---|
| ``file`` | Path to the file to upload. *(positional)* |
| `--channel` | Channel id (storage.upload_channel); minted when omitted. |
| `--backup` | Use backup.create (mode=bridge) instead of storage.upload_channel. |
| `--source` | Backup source (default: filename). |
| `--type` | Backup type (default: full). |
| `--name` | Optional task name. |
| `--priority` | Optional task priority. |
| `--interval` | Poll interval in seconds (default: 5). |

#### `bridge download`

Open a bridge channel and stream a large file FROM the storage node.

| Argument/Flag | Meaning |
|---|---|
| `--channel` | Channel id (storage.download_channel); required unless --backup is set. |
| `--backup` | Backup id (backup.restore). When set, --channel is ignored. |
| `--output, -o` | Output path (default: <channel_id> or <backup_id>). |
| `--name` | Optional task name. |
| `--priority` | Optional task priority. |
| `--interval` | Poll interval in seconds (default: 5). |

### `file`

Send/get files via the generic transfer ladder (T-164).

#### `file send`

Send a file via inline/artifact/bridge (auto-chosen).

| Argument/Flag | Meaning |
|---|---|
| ``file`` | Path to the file to send. *(positional)* |
| `--cap` | Capability that accepts the file. |
| `--force` | Force a transfer mode (must be in the capability's upload_modes). |
| `--name` | Target filename / task name. |
| `--priority` | Task priority. |
| `--owner` | Node ID that must claim the task. |
| `--source` | Backup source (backup.create bridge). |
| `--type` | Backup type (backup.create bridge). |
| `--interval` | Poll interval in seconds (bridge mode). |

#### `file get`

Get a file via inline/bridge (auto-chosen by capability).

| Argument/Flag | Meaning |
|---|---|
| ``ref`` | Generic file reference (path for storage.fetch, backup_id for backup.restore, channel_id for storage.download_channel). *(positional)* |
| `--cap` | Capability that serves the file. |
| `--output, -o` | Output path (default: filename from server/channel). |
| `--name` | Task name. |
| `--priority` | Task priority. |
| `--owner` | Node ID that must claim the task. |
| `--interval` | Poll interval in seconds (bridge mode). |

### `hp`

Handler primitives for handler scripts (T-179).

#### `hp put`

Wrap a local file as an envelope (ladder-negotiated).

| Argument/Flag | Meaning |
|---|---|
| ``path`` | Path to the local file to wrap. *(positional)* |
| `--cap` | Receiving capability (decides upload modes). |
| `--name` | Override filename inside the envelope. |

#### `hp get`

Resolve an __iowap_ref__ envelope (inline/artifact) to a local file.

| Argument/Flag | Meaning |
|---|---|
| `--file` | Read the envelope JSON from this file (default: stdin). |
| `--output, -o` | Output path (default: <out_dir>/<filename from envelope>). |
| `--out-dir` | Default drop directory (default: ~/.relay/tmp/${RELAY_TASK_ID:-adhoc}/). |

### `status`

Print worker_status.json content.

*(no additional arguments — global flags apply)*

### `reload`

Send SIGHUP to running daemon.

*(no additional arguments — global flags apply)*

### `artifact`

Artifact operations.

#### `artifact download`

Download an artifact by id from the relay.

| Argument/Flag | Meaning |
|---|---|
| ``artifact_id`` | The artifact ID to download. *(positional)* |
| `--output, -o` | Output path (default: <artifact name from server>). |

#### `artifact upload`

Upload a local file as an artifact to the relay.

| Argument/Flag | Meaning |
|---|---|
| ``file`` | Path to the file to upload. *(positional)* |
| `--name` | Artifact name (default: filename). |
| `--task-id` | Optional task ID to associate with. |
| `--stage-id` | Optional stage ID to associate with. |

### `docs`

Read relay documentation from the server (list all, or print one).

| Argument/Flag | Meaning |
|---|---|
| ``name`` | Document name (omit to list all available documents). *(positional)* |

### `update`

Check for and apply self-updates (PyPI-first, GitHub fallback).

#### `update check`

Compare installed versions (node + MCP toolkit) against upstream.

| Argument/Flag | Meaning |
|---|---|
| `--source` | Upstream: auto (PyPI→GitHub fallback, default; IOWAP_UPDATE_SOURCE), pypi (strict, no fallback) or github (legacy wheel releases). |

#### `update apply`

Update node (PyPI pip upgrade / GitHub fallback) and the MCP toolkit.

| Argument/Flag | Meaning |
|---|---|
| `--source` | Upstream for the node update: auto (PyPI→GitHub, default), pypi (strict) or github (legacy wheel download path). |
| `--no-mcp` | Skip the iowap-client-mcp check/upgrade in this run. |
| `--service-unit` | systemd user unit to restart (default: iowap-node-daemon.service). |
| `--restart-command` | Command to run instead of `systemctl --user restart` (for hosts without systemd, e.g. macOS launchd). '{unit}' is replaced with the service name. Default: RELAY_RESTART_COMMAND env or systemd. |

### `mcp`

Manage the local MCP toolkit (iowap-client-mcp).

#### `mcp install`

Install/upgrade iowap-client-mcp from PyPI into its own venv (client-neutral — wires no MCP client itself).

| Argument/Flag | Meaning |
|---|---|
| `--venv` | Toolkit venv path (default: IOWAP_MCP_VENV env or ~/iowap-client-mcp/.venv). |

#### `mcp status`

Toolkit discovery + versions (read-only).

*(no additional arguments — global flags apply)*
