# Node Configuration

The two configuration files of a node: the profile (`node.yaml`, what the
node does) and the daemon config (`relay_config.json`, how it talks).
Setup: [setup](setup.md).

## `~/.relay/node.yaml`

Central worker configuration: node-level fields plus the capability list.
The daemon reads **only** this file at runtime.

```yaml
# ~/.relay/node.yaml
node_name: felix-cyberfox
description: "Local AI worker"
status: busy                     # operator request (better: node-cli node busy)

capabilities:
  - name: chat.ai
    version: "1.0.0"
    handler: /opt/relay/handlers/chat-ai.sh
    claimable: true
    max_parallel: 2
    timeout: 300
```

### Node-level fields

| Key | Meaning |
|-----|---------|
| `node_name` | Friendly name, forwarded in every heartbeat, shown in dashboard + `node-cli node list` |
| `description` | Free-form prose (max 1024 chars), forwarded in every heartbeat |
| `status` | Operator request: `busy` / `idle` / `online` — prefer `node-cli node busy`/`idle`/`clear-status` which write it safely |
| `capabilities` | Optional list — a node can run with no capabilities and gain them at runtime |

The schema allows additional top-level keys (forward-compatible). Legacy
files (`capabilities.active.yaml`, `capabilities.d/`) are auto-migrated to
`node.yaml`/`profiles.d/` on first start of a current daemon.

### Capabilities

Full field reference (type, claimable, handler, max_parallel, timeout,
input_schema, upload_modes, config): [capabilities how-to](capabilities.md),
model: [concept: capability](../concepts/capabilities.md).

## Working profiles (`~/.relay/profiles.d/`)

Edit day-to-day profiles outside the active file, then validate and
publish atomically:

```bash
mkdir -p ~/.relay/profiles.d
cat > ~/.relay/profiles.d/default.yaml <<'YAML'
capabilities: []
YAML

node-cli capabilities validate default      # checks without touching active
node-cli capabilities publish default       # atomic write to node.yaml (+ SIGHUP)
node-cli capabilities diff                  # working profile vs active
node-cli capabilities current               # active profile name
```

The daemon never touches `profiles.d/` at runtime. Validation rejects
duplicate names, claimable-without-handler, and bad field types — on error
the active profile is untouched.

## `~/.relay/relay_config.json`

Daemon transport config (created by `node-cli relay set`, overridable by
env — env wins):

| Key (JSON) | Env | Default | Meaning |
|-----------|-----|---------|---------|
| `base_url` | `RELAY_BASE_URL` | `null` | Relay URL; `null` enables mDNS discovery fallback |
| `heartbeat_interval` | `RELAY_HEARTBEAT_INTERVAL` | `8` | Seconds between heartbeats |
| `claim_interval` | `RELAY_CLAIM_INTERVAL` | `5` | Polling-claim cadence (node-cli daemon) |
| `backfill_interval` | `RELAY_BACKFILL_INTERVAL` | `60` | Periodic sweep of the SSE daemon (0 = off) |
| `status_interval` | — | `7200` | Status-flush cadence |
| `rs_refresh_interval_seconds` | `RELAY_RS_REFRESH_INTERVAL` | `86400` | Registration-secret rotation |
| `rt_refresh_interval_seconds` | `RELAY_RT_REFRESH_INTERVAL` | `518400` | Runtime-token refresh (6 days) |
| `mdns_service_name` | `RELAY_MDNS_SERVICE_NAME` | `IOWAP Relay Service` | Discovery filter |

## File reference

| Path | Purpose |
|------|---------|
| `~/.relay/node.yaml` | Active profile — the daemon reads this |
| `~/.relay/node.profile` | Name of the active profile (auto-generated) |
| `~/.relay/profiles.d/` | Working profiles the operator edits |
| `~/.relay/relay_config.json` | Transport config (base_url, intervals) |
| `~/.relay/iowap-agent.json` | State file: node_id, registration secret, base_url pin |
| `~/.relay/iowap-agent.token` | Runtime token envelope (JSON, `expires_at`) |
| `~/.relay/worker_status.json` | Last heartbeat/self-observation (written per heartbeat) |
| `~/.relay/node-cli.pid` / `node-cli.log` | Polling-daemon PID + log |
| `~/.relay/node-daemon.pid` | SSE-daemon PID (mutual guard against co-running) |

## What it is NOT

- **Not a relay-config mirror** — server settings live on the relay host;
  `relay_config.json` only decides how *this* node talks to it.
- **Not secret storage by design** — token and secrets land in dedicated
  files (`iowap-agent.json/.token`), chmod 600 them.

## Related pages

- [operations](operations.md) — daemon control and maintenance intervals
- [capabilities how-to](capabilities.md) — the `capabilities:` entries in depth
- [token operations](tokens.md) — the credential files' lifecycle
- [glossary](../concepts/glossary.md) — terminology