# Home Assistant Node

Your Home Assistant becomes a node in the cluster — and a bridge in both
directions. Repo: [iowap-org/iowap-ha](https://github.com/iowap-org/iowap-ha)
— one repo, two installers: the Supervisor **app store** reads `iowap/`,
HACS reads `custom_components/iowap/`.

| Direction | What | How |
|-----------|------|-----|
| Cluster → HA | IOWAP tasks drive approved home capabilities | HAOS app **IOWAP Node**: node-daemon + `ha-exec` handler with a fixed capability matrix |
| HA → Cluster | Automations submit tasks into the cluster | `iowap.submit_task` service → `hassio.app_stdin` → app outbox → relay |
| HA visibility | Node health + per-capability metrics as HA entities | App-side telemetry push via the Supervisor proxy |

## Prerequisites

- A running, reachable relay ([server setup](../../server/setup.md))
- Home Assistant OS (or Supervised) with Supervisor API
- The relay URL, e.g. `http://192.0.2.60:8788`

## 1. Install the app (cluster → HA)

[![Add the IOWAP repository to your app store](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fiowap-org%2Fiowap-ha)

Or manually: Settings → Apps → App Store → ⋮ → Repositories → add
`https://github.com/iowap-org/iowap-ha`. Install **IOWAP Node**, set
`relay_url` in the options, start.

First boot: the app writes its relay config, generates the node profile
from its internal capability matrix, and registers as node `ha-app-node`
(role `worker`). It appears in the relay dashboard as `pending` — approve
it there. If the relay is offline at HA boot, registration retries every
30 s; the outbox buffers meanwhile, nothing is lost.

## 2. Install the integration (HA → cluster)

Or manually: HACS → ⋮ → Custom repositories → `https://github.com/iowap-org/iowap-ha`
(category *Integration*), then Settings → Devices & Services → Add
Integration → **IOWAP**.

## 3. Configure exposure (per domain)

Domains the matrix touches have an exposure mode, set in the integration's
**Configure** dialog and pushed to the app via `hassio.app_stdin`:

| Mode | Effect |
|------|--------|
| `on` | Full capability set (writes + reads) |
| `readonly` | State reads only — **default for every domain** |
| `off` | Domain fully invisible; reads AND writes rejected handler-side |

State survives restarts (`/data/domain_states.json`). The app options
(Settings → Apps → IOWAP Node → Configuration): `relay_url` (required),
`log_level`, `rate_limit_per_min` (default 20, per-capability),
`lock_level` (`read`/`write` — `write` publishes lock capabilities),
`status_push_interval` (default 60 s), `<domain>_entity_scope`
(glob allowlist per domain, e.g. `light.kitchen,light.living_*`).

## Capability matrix

Published from the `CAPS` table in `iowap/ha-exec.py` — the security
boundary. Payload fields are type/regex-validated against schema; keys
outside the table never reach Home Assistant; writes also respect the
entity scope and rate limit.

| Capability | HA service | Input fields |
|---|---|---|
| `ha.light.on.native` | `light.turn_on` | `entity_id`, `brightness_pct` 0–100, `color_temp_kelvin` 1500–6500, `transition` 0–60 s |
| `ha.light.off.native` | `light.turn_off` | `entity_id`, `transition` |
| `ha.light.toggle.native` | `light.toggle` | `entity_id` |
| `ha.scene.activate.native` | `scene.turn_on` | `entity_id` |
| `ha.climate.set_temperature.native` | `climate.set_temperature` | `entity_id`, `temperature` 5–35 °C |
| `ha.media.play_pause.native` | `media_player.media_play_pause` | `entity_id` |
| `ha.switch.toggle.native` | `switch.toggle` | `entity_id` |
| `ha.fan.toggle.native` | `fan.toggle` | `entity_id` |
| `ha.humidifier.toggle.native` | `humidifier.toggle` | `entity_id` |
| `ha.vacuum.start.native` | `vacuum.start` | `entity_id` |
| `ha.vacuum.return_to_base.native` | `vacuum.return_to_base` | `entity_id` |
| `ha.state.get.native` | state read (any domain) | `entity_id` |
| `ha.lock.lock.native` | `lock.lock` — **only with** `lock_level: write` | `entity_id` |
| `ha.lock.unlock.native` | `lock.unlock` — **only with** `lock_level: write` | `entity_id` |

`lock.open` does not exist and is rejected by design — opening a latch is
never available through IOWAP. A task for a domain not exposed `on` fails
with a clear deny reason (node log + handler metrics).

## Submitting tasks from HA

**Service `iowap.submit_task`** — buffered in `/data/outbox.jsonl` (fsync
per line), drained with retry by the app; a relay outage at submit time
loses nothing. Unknown capabilities fail fast with a fresh cluster view,
fail-open with an empty cache (a relay outage must not silently drop
tasks).

| Field | Required | Description |
|-------|----------|-------------|
| `capability` | yes | e.g. `agent.ai` |
| `payload` | yes | JSON payload (must satisfy the capability's input schema) |
| `name` | no | Human-readable task name |
| `priority` | no | 1–9, lower = sooner (default 5) |

```yaml
automation:
  - alias: doorbell → cluster agent
    trigger:
      - platform: state
        entity_id: binary_sensor.doorbell
        to: "on"
    action:
      - service: iowap.submit_task
        data:
          capability: agent.ai
          name: "doorbell snapshot"
          payload:
            prompt: "Someone is at the door — describe what you see."
```

**Service `iowap.get_capabilities`** — returns the cluster's offered
capabilities (options: `include_schema` default true, `available_only`
default false) for scripting via `response_variable`.

**Blueprints:** the integration generates one automation + script
blueprint per published cluster capability (`blueprints/automation/iowap/`,
`blueprints/script/iowap/`), regenerated when the capability list changes.

## Status entities in HA

Pushed every `status_push_interval` seconds (HA never polls the app):

- `binary_sensor.iowap_node_ready` — `on` while heartbeating, otherwise
  `off` with `reason`; attributes: `node_id`, `last_heartbeat`,
  `active_profile`, `capabilities`, `auth_loop`, `error`.
- `sensor.iowap_node_metrics` — state = published-capability count;
  attributes: `tasks_completed`, `tasks_failed`, `in_flight`, `per_cap`
  (calls, denied, last_call, last_outcome per capability).

## Security model

- HA core holds **no relay credentials** — the app container holds the
  only token (`/data/.relay/`) and is the single relay bridge.
- `ha-exec` enforces the matrix: `domain`+`service` never from the payload,
  entity scope validated per domain, per-capability rate limiter.
- Core→app is the `hassio.app_stdin` channel only — no network ports
  toward HA core; the app needs `hassio_role: manager`.
- **Safety automations stay local** — never couple a safety behavior to
  the relay being up.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| App start fails: no relay_url | Set `relay_url` in app options |
| Node stuck `pending` | Approve `ha-app-node` in the dashboard |
| Node never appears | Check relay_url reachability + app log |
| submit_task: unknown capability | Stale cache — check connectivity; next successful drain refreshes |
| A domain denies everything | Exposure is `readonly`/`off` → set `on` in Configure |
| Rate-limit denies | Raise `rate_limit_per_min` (default 20/min) |
| Blueprint missing | Regenerates on next integration reload once relay reachable |

## Related pages

- [node setup](../setup.md) — nodes on plain hosts
- [token operations](../tokens.md) — the rt_/rs_ credentials in the app container
- [capabilities how-to](../capabilities.md) — schemas cluster-side
- [iowap-ha repo](https://github.com/iowap-org/iowap-ha) — source