# Host setup (universal node + bridge)

Turn a desktop into a self-contained IOWAP host: the **universal node**
runs as a Docker container — the same node image every other IOWAP node
uses, no fork — and a small native **bridge daemon** on the host
bootstraps that container, registers it against your relay, and exposes
host-side applications (first target: a local ComfyUI) to the fleet as
`host.*` capabilities. Windows-first, but it runs on any Docker host
(Docker Desktop on Windows/macOS, Docker Engine on Linux).

The setup below needs no Docker CLI or GUI interaction: the daemon talks
to the Docker Engine itself and executes the
[`universal-node` compose profile](https://github.com/iowap-org/iowap-docker)
as its blueprint. Model background:
[nodes](../concepts/nodes.md) ·
[capabilities](../concepts/capabilities.md) ·
[MCP agent toolkit](../clients/mcp.md).

## 1. Install Docker

Docker Desktop on Windows (WSL2 backend) or Docker Engine on Linux.
Start it before the daemon: the daemon's bootstrap pings the engine
(named pipe on Windows, unix socket elsewhere) first and exits with an
"install or start Docker Desktop" message when it cannot reach it.

## 2. Download the bridge daemon

Grab the single executable from the
[releases page](https://github.com/iowap-org/iowap-bridge-daemon/releases)
of the `iowap-bridge-daemon` repo — for Windows:
`iowap-bridge-windows-amd64.exe` (release assets are published with each
`v*` tag). Every asset has a sibling `.sha256`
file — verify before running:

```powershell
Get-FileHash .\iowap-bridge-windows-amd64.exe -Algorithm SHA256
# -> compare against the value in iowap-bridge-windows-amd64.exe.sha256
```

The binary is unsigned: Windows SmartScreen shows a one-time warning on
first launch — "More info" → "Run anyway".

## 3. Start the daemon (bootstrap)

Run the `.exe`. On the first start the daemon bootstraps everything:

1. Engine check (see step 1).
2. If the `iowap-universal-node` container is not already running: image
   pull and container creation via the vendored `universal-node` compose
   profile — with the bridge token and a freshly generated MCP bearer
   injected as environment variables.
3. The onboarding web UI opens its port (see step 4).

A later daemon start that finds the container already running skips the
bootstrap entirely — same container, no new tokens.

## 4. Register the node in the web UI

Open `http://127.0.0.1:7782` in the browser on the same host. The page
shows the container status and a small form: **node name** and **server
host:port**. The server field is pre-filled when mDNS discovery inside
the container finds an advertising relay; otherwise enter the relay
address (`host:port` or URL, e.g. `192.0.2.10:8788`).

Submit → the daemon runs `iowap-cli node register <server> --name <name>`
inside the container. From there the node takes over by itself: it
writes its config, starts heartbeating. While `pending`, an admin must
approve it (dashboard **Nodes → Approve** — see
[server admin](../server/admin.md)); after approval the node shows
`online` in the [dashboard](../server/dashboard.md).

## 5. Connect your agents (one-time MCP bearer)

After a bootstrap the UI displays the MCP bearer (`iw_mcp_…`) **exactly
once**, together with ready-made config snippets. Copy it now —
afterwards the daemon keeps only its SHA-256 hash, a daemon restart
shows nothing, and rotation means recreating the container.

The snippets below use `<bearer>` where the UI inserts the real value.
The endpoint is loopback-only on `127.0.0.1:7781`.

Hermes (one-liner, then `/reload-mcp` or a new session):

```bash
hermes mcp add iowap --url http://127.0.0.1:7781/mcp --header "Authorization: Bearer <bearer>"
```

Claude Desktop / Claude Code (`mcpServers` JSON):

```json
{
  "mcpServers": {
    "iowap": {
      "type": "http",
      "url": "http://127.0.0.1:7781/mcp",
      "headers": { "Authorization": "Bearer <bearer>" }
    }
  }
}
```

Codex (`config.toml`):

```toml
[mcp_servers.iowap]
url = "http://127.0.0.1:7781/mcp"
http_headers = { "Authorization" = "Bearer <bearer>" }
```

Generic live probe:

```bash
curl -H "Authorization: Bearer <bearer>" http://127.0.0.1:7781/mcp
# -> authenticated request succeeds; missing/wrong bearer gets 401
```

What the agent gets: the curated IOWAP toolset over MCP — tool
reference and security boundary in
[MCP toolkit](../clients/mcp.md) (the HTTP transport variant).

## 6. Publish host capabilities (opt-in)

The node polls the daemon's manifest and detects provider capabilities
(e.g. `comfy.generate`). Publishing is **conservative by default**:
without an explicit opt-in, detected caps are logged but never published
to the relay. To switch them on, add a `bridge:` block to the node's
`node.yaml` (inside the container at `~/.relay/node.yaml`; the state
volume keeps it across restarts):

```yaml
bridge:
  url: http://host.docker.internal:7780
  token: ""              # empty = use the injected IOWAP_BRIDGE_TOKEN env
  workspace: /workspace  # the shared workspace volume root
  auto_publish: false    # conservative default: detect + log only
  allowlist: []          # explicit opt-in, e.g. ["comfy.generate"] or ["*"]
  poll_interval: 60
```

Gate semantics: an allowlist entry (or `["*"]`) publishes exactly the
listed names; `auto_publish: true` publishes everything **only** while
the allowlist is empty — a non-empty allowlist always wins. Config
changes are picked up on the next manifest poll, no daemon restart
needed. Published caps appear in the fleet as `host.<name>` and are
claimed like any other capability. The [glossary](../concepts/glossary.md)
defines the vocabulary.

## Ports

All three ports are loopback-only — reachable from this host, never from
the network:

| Port | Purpose | Binding |
|------|---------|---------|
| 7780 | Bridge manifest/exec API (node container → daemon) | `127.0.0.1` |
| 7781 | HTTP MCP endpoint (agents → node container) | `127.0.0.1` |
| 7782 | Onboarding web UI (browser, this host) | `127.0.0.1` |

## Environment variables

Daemon-side settings (set as ordinary environment variables before
starting the daemon). The two tokens are injected into the container
under the same names at bootstrap — you never set them by hand:

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `IOWAP_BRIDGE_TOKEN` | yes | — | Bearer token for the bridge API; fail-closed — the daemon exits without it. Injected into the container at bootstrap. |
| `IOWAP_MCP_BEARER` | no | generated | MCP bearer for agents. Generated by the daemon at container creation, injected into the container, displayed once (step 5). |
| `IOWAP_MCP_PORT` | no | `7781` | MCP port shown in the UI snippets (the real mapping lives in the compose profile). |
| `IOWAP_WORKSPACE_DIR` | no | `./workspace` | Workspace root shared with the container (mounted at `/workspace`) — artifact hand-off. |
| `IOWAP_COMFYUI_URL` | no | `http://127.0.0.1:8188` | ComfyUI base URL for the host-side provider. |
| `IOWAP_COMFYUI_CMD` | no | — | Optional command to (re)start ComfyUI when its health probe fails. |
| `IOWAP_BRIDGE_PORT` | no | `7780` | Bridge API port (loopback only). |
| `IOWAP_UI_PORT` | no | `7782` | Onboarding UI port (loopback only). |

## Verification

```bash
docker ps --filter name=iowap-universal-node --format "{{.Names}} {{.Status}}"
# -> iowap-universal-node   Up ...
```

- Web UI on `http://127.0.0.1:7782` shows the container running and the
  registered node name.
- The node appears `online` in the dashboard; the daemon log line
  `bridge: published host caps: …` confirms opt-in publishing worked.
- The MCP probe from step 5 answers without `401`.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Daemon exits with "install or start Docker Desktop" | The engine check failed — start Docker Desktop (or Docker Engine) and run the daemon again. |
| Container crash-loops | Likely a stale cached node image missing the blank-start/bridge features. Remove the container (`docker rm -f iowap-universal-node`), pull the current `ghcr.io/iowap-org/iowap-node-base` image, and start the daemon again — bootstrap recreates the container from the fresh image. |
| `host.*` capability does not appear | The publish gate is conservative by default — check the `bridge:` block in the node's `node.yaml`: a cap publishes only when it is in `allowlist` (or `["*"]`), or when `auto_publish: true` and the allowlist is empty. The node logs detected-but-gated caps. |
| Node stays `pending` | Admin must approve it — dashboard **Nodes → Approve** ([server admin](../server/admin.md)). |
| MCP bearer lost / never copied | One-time display — recreate the container to rotate (a daemon restart alone never re-shows it). |
| `401` from the MCP endpoint | Wrong or missing bearer in the agent config — compare against the snippet from step 5. |
| Relay not found in the UI form | mDNS discovery found nothing — type the relay address manually, or check that the relay advertises mDNS. |

## Related pages

- [MCP toolkit](../clients/mcp.md) — the agent-facing toolset (stdio and HTTP transport)
- [node setup](setup.md) — the classic host-native node installation
- [capabilities how-to](capabilities.md) — profiles and publishing
- [server docker](../server/docker.md) — relay in a container
- [iowap-bridge-daemon](https://github.com/iowap-org/iowap-bridge-daemon) — daemon repo (release binaries, manifest/exec contract)
