# IOWAP for Hermes Desktop (Hermes Integration Plugin)

Drive the IOWAP fleet straight from your [Hermes](https://hermes-agent.nousresearch.com)
desktop app — no browser, no dashboard detour:

| Surface | What | Where |
| --------- | ------ | ------- |
| Statusbar chip | Live dot + `N/M` nodes online, one click opens the fleet page | Bottom bar, always visible |
| Fleet pane | Compact node list docked in the right zone (draggable) | Right zone |
| Fleet page `/iowap-fleet` | Full overview: status, load, queue depth, per-node capabilities, Activity section (daemon self-sight, tracked tasks, task-capability provider health) | Sidebar nav + ⌘K |
| Tasks page `/iowap-tasks` | Submit a task to any task-type capability, track tasks by relay id, watch tracked tasks live (per-stage status dots, result previews, artifacts) | Sidebar nav + ⌘K |
| ⌘K commands | Refresh fleet data, notify fleet status, open the pages | Palette |

The Hermes desktop app is **not** an IOWAP node — it is a control surface. It
submits and watches tasks, it does not register as an executor.

Repo: [iowap-org/iowap-hermes-integration](https://github.com/iowap-org/iowap-hermes-integration)

## Architecture

```text
desktop renderer (plugin.js)        gateway process (plugin_api.py)        relay
┌─────────────────────┐   ctx.rest  ┌──────────────────────────┐  node-cli  ┌───────┐
│ chip / pane / page  │ ──────────► │ /api/plugins/iowap/fleet │ ─────────► │ :8788 │
└─────────────────────┘             └──────────────────────────┘            └───────┘
```

The desktop **frontend** never touches relay HTTP or tokens. The **backend**
(`/api/plugins/iowap/*`) shells out to `node-cli --json`, which owns all relay
auth and token handling (`~/.relay/*`). Relay tokens never enter the renderer.

## Prerequisites

- Hermes Agent with the desktop app and plugin support
- `node-cli` ([iowap-node](https://github.com/iowap-org/iowap-node), pip) on
  the desktop host
- A registered, approved node on the relay — `~/.relay/iowap-agent.*` must
  exist (see [setup.md](setup.md)); the backend reuses that node
  identity and its token

## Installation

Both halves come from the repo; the plugin id is `iowap` (the desktop folder
name must match it).

**Desktop half** (chip, pane, pages, commands) → `~/.hermes/desktop-plugins/iowap/`:

```bash
mkdir -p ~/.hermes/desktop-plugins/iowap
curl -o ~/.hermes/desktop-plugins/iowap/plugin.js \
  https://raw.githubusercontent.com/iowap-org/iowap-hermes-integration/main/desktop/plugin.js
```

**Backend half** (fleet data through node-cli) → `~/.hermes/plugins/iowap/dashboard/`:

```bash
mkdir -p ~/.hermes/plugins/iowap/dashboard
curl -o ~/.hermes/plugins/iowap/dashboard/manifest.json \
  https://raw.githubusercontent.com/iowap-org/iowap-hermes-integration/main/dashboard/manifest.json
curl -o ~/.hermes/plugins/iowap/dashboard/plugin_api.py \
  https://raw.githubusercontent.com/iowap-org/iowap-hermes-integration/main/dashboard/plugin_api.py
hermes config set plugins.enabled '["iowap"]'
```

Then **restart the Hermes desktop app** — the backend imports live in the
gateway process, a plugin reload is not enough the first time — and run
**Reload desktop plugins** (⌘K) afterwards for frontend edits. Enable the
desktop half in **Capabilities → Plugins** if it stays off.

### Update

From a repo checkout:

```bash
tools/deploy.sh   # copies both halves, verifies md5; frontend hot-reloads,
                  # backend edits need one app restart
```

## Tasks page

- **Submit**: pick a task-type capability, enter the payload as JSON,
  optionally name the task. The submit runs through the relay scheduler
  (`task-simple`-equivalent via node-cli).
- **Track**: enter a relay task id or watch tracked tasks live — per-stage
  status dots, result previews, artifacts.
- **Delegated rows**: tasks the agent submitted owner-directed
  (`--owner <node_id>` via the `iowap-task` session bridge) show as
  `delegated` — the result is unreadable from this node by design
  (server-side owner scoping), not an error.

### Session bridge (agent → track store)

Tasks submitted from agent sessions via `tools/iowap-task` (installed at
`~/.local/bin/iowap-task`, wraps `node-cli task submit`) merge into the shared
flock-protected track store `~/.hermes/cache/task-track-iowap.json` — the
tasks page shows them alongside UI submissions, same status dots.

## Troubleshooting

| Symptom | Cause / fix |
| --------- | ------------- |
| UI shows an error hint | Backend half missing or broken — the frontend degrades gracefully without it; reinstall the backend files or check `hermes config get plugins.enabled` |
| No fleet data after backend edit | Backend imports live in the gateway process — restart the app, a plugin reload suffices only for frontend edits |
| Auth errors on every call | No node state — the backend reuses `~/.relay/iowap-agent.*`; register and approve a node first (see [setup.md](setup.md)) |
| Chip shows online but no data | Relay reachable (`/health` is unauthenticated) but tokens stale — check the node's token lifecycle (see [token-lifecycle.md](token-lifecycle.md)) |

## Version

Current: **v0.3.0** — chip, pane, fleet page, palette commands, tasks page
(submit / track / delegated), live data via node-cli, session bridge. This
page documents v0.3.x; check the repo README for newer behavior.

## License

MIT — see [LICENSE](LICENSE).