# Host setup (universal node + bridge)

Turn a desktop into a self-contained IOWAP host: the **universal node**
runs as a Docker container — the dedicated **universal-node flavour
image** (built on top of the plain node framework image, see below) —
and a small native **bridge daemon** on the host
bootstraps that container, registers it against your relay, and exposes
host-side applications (first target: a local ComfyUI) to the fleet as
`host.*` capabilities. Windows-first, but it runs on any Docker host
(Docker Desktop on Windows/macOS, Docker Engine on Linux).

Current stack (2026-11 release set): container image
`ghcr.io/iowap-org/iowap-universal-node:latest` — node framework
**2.3.66** with the MCP multi-bearer surface (**14 tools**, agent
tokens with per-task binding) — and bridge daemon **bridge-v0.3.7**
(exec contract v1.1: the daemon is a *dumb executor*, it runs the spec
the node sends instead of resolving capability names). The image builds
on the plain `iowap-node-base` framework image — the flavour parts (the
streaming-HTTP MCP surface and the bootstrap) live in the
[`iowap-universal-node`](https://github.com/iowap-org/iowap-universal-node)
repo and get baked by CI.

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

Grab the single executable from the releases of the
[`iowap-universal-node`](https://github.com/iowap-org/iowap-universal-node/releases)
repo — **GitHub Releases are the canonical channel** (public, hashable,
one release per `bridge-v*` tag). For Windows download:
`iowap-bridge-windows-amd64.exe`. Every asset has a sibling `.sha256`
file — verify before running:

```powershell
Get-FileHash .\iowap-bridge-windows-amd64.exe -Algorithm SHA256
# -> compare against the value in iowap-bridge-windows-amd64.exe.sha256
```

The running tray checks the same channel via the releases API and
notifies when a newer `bridge-v*` version exists. (Nextcloud
`Shared/iowap-bridge/` mirrors every release for convenience — it is the
private test channel, not the canonical one.)

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
[MCP toolkit](../clients/mcp.md) (the HTTP transport variant,
**14 tools** including the capability-management tools).

## 5b. Agent tokens (per-agent MCP access)

Since the multi-bearer update the bearer shown at bootstrap is the
**primary** token (full access, never shown again). For every extra MCP
client create an **agent token** in the node dashboard (section
“Agent-Tokens” on the web UI):

- **Create** → the raw token is displayed **exactly once**
  (show-once); the node stores only its SHA-256 hash in the
  `iowap-agent-tokens` volume — not on the Explorer-visible workspace.
- Every agent task is **bound to its token**: `task_result`,
  `artifact_download` and `artifact_link` only answer for tasks that
  this agent submitted. A different agent asking for the same task
  gets the same “not found” answer as asking for a task that does not
  exist — ownership leaks nothing.
- **Capability management is opt-in per token** (`caps:manage` toggle):
  without the flag the capability create/update/publish tools answer
  “restricted for this token”.
- **Revoke** flips the token off immediately (401) and keeps the
  binding history in the store.

The primary bearer stays untouched and keeps full access.

## 6. Publish host capabilities (manual, checkbox model)

The node polls the daemon's manifest and detects provider capabilities
(e.g. `comfy.generate`). Publishing is **manual and per-capability**:
a newly detected or dashboard-created capability starts unpublished and
stays invisible to the relay until you publish it.

On the dashboard's capability table every row carries a **checkbox**
showing the current published state. Tick the capabilities that should
go live, untick the ones that should be pulled back, then press
**“Update Capabilities”** — one call applies the whole set and flashes
`published: N, unpublished: M, unchanged: K`. Programmatically the same
works via `capability_publish(published=true/false)` on the MCP
service surface.

Under the hood every publish change (and every capability
create/edit/delete) automatically recomposes the active `node.yaml`
from the allowlist-filtered entries — the daemon gets a reload, and
the relay receives the new full capability list on the next heartbeat.
Because the worker heartbeat is a **full replace**, pulling a
capability back deletes it from the relay's discovery automatically.

Underlying config (inside the container at `~/.relay/node.yaml`; the
state volume keeps it across restarts):

```yaml
bridge:
  url: http://host.docker.internal:7780
  token: ""
  workspace: /workspace
  allowlist: ["comfy.generate", "host.sysinfo"]   # the publish state
  poll_interval: 60
```

A legacy `bridge:` block with `auto_publish: true` and an empty
allowlist is migrated once on the first bridge-block write after the
update: the allowlist is seeded with the then-current capability names
and `auto_publish` turns off — the live state is conserved, from then
on everything is manual. `auto_publish` itself stays a valid opt-in
flag for local-handler profiles.

## 6b. Budget and busy (node dashboard)

The dashboard's **Budget & Busy** section:

- **Budget** — an accounting budget (set 10, 100 or whatever your
  scale is). Every completed capability task adds its `cost` to a
  persistent meter shown as `used N / budget B (P%)` next to a
  reset button. The budget also feeds the claim-admission axis, so
  the value is never silently disarmed. No automatic busy at 100% —
  the switch below is yours to flip.
- **Busy switch** — a manual override that persists in the config and
  rides every heartbeat: while busy the node claims nothing and shows
  `busy` in the fleet; switching it off reverts to `idle`.

## 6c. Forward slots (define + routing)

Forward slots let a service address one of this node's capabilities by
a stable name instead of a concrete task. In the dashboard's forward
section you **define** slots directly (label, typed
`forward`/`text`/`bool`, value and ref fields for typed slots) — the
definition lands in the `forward_slots` section of `node.yaml` and
rides every heartbeat. The `(node, slot) → target_capability`
mappings are maintained by an admin on the relay side; full semantics
(including which slots are routable and how a mapped submit reaches a
pinned target): [forward routing](../concepts/forward-routing.md)
— slots as the service side of the nodes.

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
| Container image is stale after a stack update | Remove the container (`docker rm -f iowap-universal-node`) and `docker compose pull && up -d` (or let the daemon recreate it) — the daemon pulls `ghcr.io/iowap-org/iowap-universal-node`, which carries the current node framework and MCP surface. |
| `host.*` capability does not appear | Publishing is manual: tick the capability row and press **“Update Capabilities”** on the dashboard (or create a `bridge.allowlist` entry). A legacy block with `auto_publish: true` and an empty allowlist migrates itself on the first bridge-block write — otherwise the node logs detected-but-unpublished caps. |
| Checkbox publish “didn't take” | The batch needs node ≥ 2.3.65 (the recompose pipeline lives in the wheel) — check `pip show iowap-node` inside the container after pulling the image. |
| Agent A does not see agent B's task results | Per-task binding is by design — `task_result`/`artifact_download` of another agent answer `not_found`. Use the primary bearer for operator-wide read access. |
| Node stays `pending` | Admin must approve it — dashboard **Nodes → Approve** ([server admin](../server/admin.md)). |
| MCP bearer lost / never copied | One-time display for the primary bearer — recreate the container to rotate. Agent tokens (5b) can be created/revoked freely in the dashboard instead. |
| `401` from the MCP endpoint | Wrong or missing bearer in the agent config — compare against the agent token from section 5b or the bootstrap snippet (primary bearer). |
| Relay not found in the UI form | mDNS discovery found nothing — type the relay address manually, or check that the relay advertises mDNS. |

## Related pages

- [MCP toolkit](../clients/mcp.md) — the agent-facing toolset (stdio and HTTP transport)
- [node setup](setup.md) — the classic host-native node installation
- [capabilities how-to](capabilities.md) — profiles and publishing
- [server docker](../server/docker.md) — relay in a container
- [iowap-bridge-daemon](https://github.com/iowap-org/iowap-bridge-daemon) — daemon repo (release binaries, manifest/exec contract)
