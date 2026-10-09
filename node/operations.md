# Node Operations

Day-to-day operation of a node: daemon variants, status control, and the
maintenance machinery. Setup: [setup](setup.md).

## Daemon variants

Two daemons ship with iowap-node; both share the same config, token, and
capability profile — only the claim mechanism differs:

| Aspect | `node-cli daemon` | `node-daemon` (SSE) |
|--------|-------------------|---------------------|
| Mechanism | Poll the claim endpoint (every `claim_interval`, default 5 s) | Subscribe to the event stream; claim on `task_created`/`stage_claimed` |
| Latency | ≤ poll interval | Real-time |
| Requests | ~720/h claim calls | 1 persistent stream + heartbeat |
| Extra | — | Periodic backfill sweep (default 60 s) rescues missed one-shot events |

**Rule of thumb: SSE (`node-daemon`) first, polling as fallback.** Pick
polling behind proxies/firewalls that break long-lived streams (symptom:
constant reconnects while heartbeats succeed), on flaky mobile links, or
for the simplest possible setup.

**Never run both for the same node.** Both refresh the same runtime token
— each refresh invalidates the other's (401 loops, duplicate execution).
Both daemons check each other's PID file at startup and refuse to run
together; a stale PID file from a crashed process does not block.

Quick reference:

```bash
node-cli daemon start        # background, PID+log under ~/.relay/
node-cli daemon status
node-cli daemon stop
node-cli daemon foreground   # terminal foreground run

node-daemon --foreground     # SSE variant, foreground
systemctl --user enable --now iowap-node-daemon.service   # SSE variant as service
```

## Status control

```bash
node-cli node busy          # stop claiming new stages; running ones continue
node-cli node idle          # back to available
node-cli node clear-status  # drop the operator request entirely
node-cli node status        # local + server view (--json, --once supported)
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

`node-daemon` and `node-cli daemon` share the `RelayClient` self-healing:

- Token reload from file when a refresh + recovery fails;
- Exponential backoff (10 → 20 → 40 → 80 → 160 s, max 300 s) from the
  third consecutive 401/403 — applied to the heartbeat loop;
- `worker_status.json` flips to degraded (`auth_loop: true` +
  `auth_backoff_seconds`); backoff resets on first success.

The SSE reconnect stays on its own fixed delay (network/server-restart
causes are independent of auth problems).

## Server health probe

Both daemons probe `/health`, `/ready`, and `/metrics` on a 30 s cadence
(own thread — a hanging HTTP call never stalls heartbeats). Results land
in `worker_status.json` and surface in `node-cli status`.

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