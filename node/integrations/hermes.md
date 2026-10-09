# Hermes Desktop Integration

Drive the IOWAP fleet straight from the
[Hermes](https://hermes-agent.nousresearch.com) desktop app — no browser,
no dashboard detour. Repo:
[iowap-org/iowap-hermes-integration](https://github.com/iowap-org/iowap-hermes-integration)
(plugin id `iowap`, current version `0.3.0`).

The desktop app is **not an IOWAP node** — it is a control surface: it
submits and watches tasks, it does not register as an executor.

| Surface | What | Where |
| -------- | ------ | ------- |
| Statusbar chip | Live dot + `N/M` nodes online, click opens the fleet page | Bottom bar |
| Fleet pane | Compact node list (draggable) | Right zone |
| Fleet page `/iowap-fleet` | Status, load, queue depth, capabilities, Activity (daemon self-sight, tracked tasks, provider health) | Sidebar + ⌘K |
| Tasks page `/iowap-tasks` | Submit to any task-type capability, track by relay id, live per-stage dots, result previews, artifacts | Sidebar + ⌘K |
| ⌘K commands | Refresh fleet data, notify fleet status, open pages | Palette |

## Architecture

```text
desktop renderer (plugin.js)        gateway process (plugin_api.py)        relay
┌─────────────────────┐   ctx.rest  ┌──────────────────────────┐  node-cli  ┌───────┐
│ chip / pane / page  │ ──────────► │ /api/plugins/iowap/fleet │ ─────────► │ :8788 │
└─────────────────────┘             └──────────────────────────┘            └───────┘
```

The frontend never touches relay HTTP or tokens. The backend
(`/api/plugins/iowap/*`) shells out to `node-cli --json`, which owns all
relay auth and token handling (`~/.relay/*`) — tokens never enter the
renderer.

## Prerequisites

- Hermes Agent with the desktop app and plugin support
- `node-cli` ([iowap-node](https://github.com/iowap-org/iowap-node), pip)
  on the desktop host
- A registered, approved node identity on the relay —
  `~/.relay/iowap-agent.*` must exist (see [node setup](../setup.md));
  the backend reuses that identity and its token

## 1. Install the desktop half

Frontend files → `~/.hermes/desktop-plugins/iowap/`:

```bash
mkdir -p ~/.hermes/desktop-plugins/iowap
curl -o ~/.hermes/desktop-plugins/iowap/plugin.js \
  https://raw.githubusercontent.com/iowap-org/iowap-hermes-integration/main/desktop/plugin.js
```

## 2. Install the backend half

Backend files → `~/.hermes/plugins/iowap/dashboard/`:

```bash
mkdir -p ~/.hermes/plugins/iowap/dashboard
curl -o ~/.hermes/plugins/iowap/dashboard/manifest.json \
  https://raw.githubusercontent.com/iowap-org/iowap-hermes-integration/main/dashboard/manifest.json
curl -o ~/.hermes/plugins/iowap/dashboard/plugin_api.py \
  https://raw.githubusercontent.com/iowap-org/iowap-hermes-integration/main/dashboard/plugin_api.py
hermes config set plugins.enabled '["iowap"]'
```

Then **restart the Hermes desktop app** — backend imports live in the
gateway process, a plugin reload is not enough the first time. Frontend
edits hot-reload via **Reload desktop plugins** (⌘K). Enable the desktop
half in **Capabilities → Plugins** if it stays off.

**Update** from a checkout: `tools/deploy.sh` — copies both halves,
verifies md5; frontend hot-reloads, backend edits need one app restart.

## Tasks page

- **Submit:** pick a task-type capability, enter the payload as JSON,
  optionally name the task — through the relay scheduler (task-simple
  equivalent via node-cli).
- **Track:** enter a relay task id or watch tracked tasks live — per-stage
  status dots, result previews, artifacts.
- **Delegated rows:** tasks submitted owner-directed
  (`--owner <node_id>` via the `iowap-task` session bridge) show as
  `delegated` — the result is unreadable from this node by design
  (server-side owner scoping), not an error.

### Session bridge (agent → track store)

Tasks submitted from agent sessions via `tools/iowap-task`
(~/.local/bin/iowap-task, wraps `node-cli task submit`) merge into the
shared flock-protected track store `~/.hermes/cache/task-track-iowap.json`
— the tasks page shows them alongside UI submissions with the same status
dots.

## Verification

```bash
ls ~/.hermes/plugins/iowap/dashboard/plugin_api.py
# -> file exists (backend half installed)
hermes config get plugins.enabled
# -> contains "iowap"
node-cli status
# -> an approved node identity exists for the backend to reuse
```

## Troubleshooting

| Symptom | Cause / fix |
| --------- | ------------- |
| UI shows an error hint | Backend missing/broken — frontend degrades gracefully; reinstall backend files, check `plugins.enabled` |
| No fleet data after backend edit | Gateway process needs a full app restart |
| Auth errors on every call | No node identity — register + approve a node first ([setup](../setup.md)) |
| Chip online but no data | Relay reachable but tokens stale — see [token operations](../tokens.md) |

## Related pages

- [node setup](../setup.md) — the node identity this integration reuses
- [CLI reference](../cli.md) — what the backend shells out to
- [iowap-hermes-integration repo](https://github.com/iowap-org/iowap-hermes-integration) — source