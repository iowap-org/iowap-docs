# Node Operations

Day-to-day operation of a node: daemon modes, status control, and the
maintenance machinery. Setup: [setup](setup.md).

## Daemon modes

The daemon ships as one binary — `iowap-daemon` — with two modes; both
share the same config, token, and capability profile — only the claim
mechanism differs:

| Aspect | `--mode sse` (default) | `--mode poll` |
|--------|------------------------|---------------|
| Mechanism | Subscribe to the event stream; claim on `task_created`/`stage_claimed` | Poll the claim endpoint (every `claim_interval`, default 5 s) |
| Latency | Real-time | ≤ poll interval |
| Requests | 1 persistent stream + heartbeat | ~720/h claim calls |
| Extra | Periodic backfill sweep (default 60 s) rescues missed one-shot events | — |
| PID + log | `~/.relay/node-daemon.pid` + `node-daemon.log` | `~/.relay/node-cli.pid` + `node-cli.log` |

**Rule of thumb: SSE first, polling as fallback.** Pick polling behind
proxies/firewalls that break long-lived streams (symptom: constant
reconnects while heartbeats succeed), on flaky mobile links, or for the
simplest possible setup.

**Never run both modes for the same node.** Both refresh the same runtime
token — each refresh invalidates the other's (401 loops, duplicate
execution). Both modes check each other's PID file at startup and refuse
to run together; a stale PID file from a crashed process does not block.

## Starting and stopping

The daemon always runs in the foreground — backgrounding is a service
manager's job (systemd user unit pattern: [setup](setup.md)):

```bash
iowap-daemon                    # start in the foreground (SSE, default)
iowap-daemon --mode poll        # foreground, legacy claim/heartbeat polling
systemctl --user enable --now iowap-daemon.service     # run as a service
systemctl --user stop iowap-daemon.service             # stop the service
```

A plain foreground run stops with `Ctrl+C` / `SIGTERM`.

## Daemon status

```bash
iowap-daemon status             # same output via --status flag
# -> pid: 899388
# -> mode: sse
# -> running: True
# -> active_profile: default
# -> last_heartbeat: 2026-11-18T15:48:58.745477+00:00
# -> heartbeat_status: ok
```

Read-only (no relay client): a mode-aware view across both PID files
(SSE `node-daemon.pid`, poll `node-cli.pid`); exit `0` with a live
daemon, `1` when none runs. The same fields land in `worker_status.json`
— its `daemon` entry names the invoked binary (`iowap-daemon`, or
`node-daemon` under the legacy alias); the full dump also carries the
task counters and the `in_flight` queue (`iowap-cli status` prints it
all).

## Status control

```bash
iowap-cli node busy          # stop claiming new stages; running ones continue
iowap-cli node idle          # back to available
iowap-cli node clear-status  # drop the operator request entirely
iowap-cli node status        # local + server view (--json, --once supported)
```

The request is written into `node.yaml` (text-preserving — comments and
ordering survive, no YAML re-serialisation) and forwarded on every
heartbeat. The server validates the transition; invalid ones are ignored.
Auto-busy rules (load cap, GPU queue depth):
[nodes](../concepts/nodes.md) and the scheduler notes in
[tasks](../concepts/tasks.md).

## Token maintenance (automatic)

The daemon maintains credentials on fixed intervals — no operator action:

| Credential | TTL | Daemon behaviour |
|-----------|-----|------------------|
| Runtime token (`rt_…`) | 7 days | refresh every 6 days (`rt_refresh_interval_seconds`); proactive refresh inside the heartbeat loop when expiry < 1 h |
| Registration secret (`rs_…`) | 7 days | rotate on every start + every 24 h (`rs_refresh_interval_seconds`) |

Rotations run inside a **quiescence window** (SSE held, claims paused) so
an 8 s heartbeat tick never drops the stream for nothing. Manual flows:
[token operations](tokens.md).

## Auth-failure backoff

The daemon shares the `RelayClient` self-healing across both modes:

- Token reload from file when a refresh + recovery fails;
- Exponential backoff (10 → 20 → 40 → 80 → 160 s, max 300 s) from the
  third consecutive 401/403 — applied to the heartbeat loop;
- `worker_status.json` flips to degraded (`auth_loop: true` +
  `auth_backoff_seconds`); backoff resets on first success.

The SSE reconnect stays on its own fixed delay (network/server-restart
causes are independent of auth problems).

## Server health probe

Both modes probe `/health`, `/ready`, and `/metrics` on a 30 s cadence
(own thread — a hanging HTTP call never stalls heartbeats). Results land
in `worker_status.json` and surface in `iowap-cli status`.

## What it is NOT

- **Not a supervisor for handlers** — handler processes are per-stage
  children with their own timeout budget, not long-lived services.
- **Not cluster-aware** — a node knows its own state; fleet-wide views are
  the dashboard's job.

## Related pages

- [setup](setup.md) — installation and registration
- [config](config.md) — `node.yaml` and `relay_config.json`
- [token operations](tokens.md) — manual credential flows
- [CLI reference](cli.md) — every command and flag