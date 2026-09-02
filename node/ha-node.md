# IOWAP for Home Assistant (HAOS App + Integration)

Your Home Assistant becomes a first-class node in the IOWAP cluster — and a
bridge in both directions:

| Direction | What | How |
|-----------|------|-----|
| Cluster → HA | IOWAP tasks drive approved home capabilities (lights, climate, scenes, state reads) | HAOS app **IOWAP Node**: node-daemon + `ha-exec` handler with a fixed capability matrix |
| HA → Cluster | Automations and scripts submit tasks into the cluster (e.g. smoke detected → `agent.ai`) | `iowap.submit_task` service → `hassio.app_stdin` → app outbox → relay |
| HA visibility | Node health, relay status, per-capability metrics as HA entities | App-side telemetry push via the Supervisor proxy |

Repo: [iowap-org/iowap-ha](https://github.com/iowap-org/iowap-ha) — one repo,
two installers: the Supervisor **app store** reads `iowap/`, HACS reads
`custom_components/iowap/`.

## Prerequisites

- A running, reachable relay server (see [../server/setup.md](../server/setup.md))
- Home Assistant OS (or Supervised) with the Supervisor API
- The relay URL, e.g. `http://192.168.2.60:8788`

## Installation

### App (cluster → HA)

[![Open your Home Assistant instance and add the IOWAP repository to your app store.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fiowap-org%2Fiowap-ha)

Or manually: Settings → Apps → App Store → ⋮ → Repositories → add
`https://github.com/iowap-org/iowap-ha`. Install **IOWAP Node**, set your
`relay_url` in the app options, start.

On first boot the app writes its relay config, generates the node profile from
its internal capability matrix and registers against the relay as node
`ha-app-node` (role `worker`). The node appears in your relay dashboard for
approval (status `pending`); approve it there. The runtime token is minted at
approval-time refresh. If the relay is offline at HA boot, registration retries
every 30 s — the outbox buffers meanwhile, nothing is lost.

### Integration (HA → cluster)

[![Open your Home Assistant instance and add the IOWAP repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fiowap-org%2Fiowap-ha&category=integration)

Or manually: HACS → ⋮ → Custom repositories → `https://github.com/iowap-org/iowap-ha`,
category *Integration*. Then Settings → Devices & Services → Add Integration →
**IOWAP**.

## App options

All options are set in Settings → Apps → IOWAP Node → Configuration. Empty
options use the documented default; the schema validates input before the app
ever sees it.

| Option | Type / default | Purpose |
|--------|----------------|---------|
| `relay_url` | url, **required** | Relay base URL, e.g. `http://192.168.2.60:8788` |
| `log_level` | `trace`…`ERROR` (default `INFO`) | App log verbosity |
| `rate_limit_per_min` | int 1–120 (default 20) | Per-capability call limit; throttles runaway automations |
| `lock_level` | `read` \| `write` (default `read`) | `write` additionally publishes the lock/unlock capabilities |
| `status_push_interval` | int 15–3600 s (default 60) | How often the app pushes node state into HA |
| `<domain>_entity_scope` | glob per domain (default `*`) | Entity allowlist per domain — see below |

Supported domains for `<domain>_entity_scope`: `light`, `climate`, `switch`,
`fan`, `humidifier`, `vacuum`, `media_player`, `scene`. A scope is a
glob/glob-list matched against entity IDs, e.g. `light.hue_*` or
`light.kitchen,light.living_*`.

## Domain exposure (per-domain on / readonly / off)

Every domain the capability matrix touches has an exposure mode, set in the
integration's **Configure** dialog (options flow) and pushed to the app via the
official `hassio.app_stdin` channel:

| Mode | Effect |
|------|--------|
| `on` | Full capability set for the domain (writes + reads) |
| `readonly` | State reads only — write capabilities for the domain are unpublished |
| `off` | Domain fully invisible; reads AND writes rejected handler-side |

**Default for every domain is `readonly`.** The state is persisted in
`/data/domain_states.json` and survives app restarts.

## Capability matrix

Published automatically from the `CAPS` table in `iowap/ha-exec.py` — the
single source of truth. Input schemas are generated at profile bootstrap;
every payload field is type/regex-validated and keys outside this table never
reach Home Assistant. All write capabilities are also subject to per-domain
entity scope and the per-capability rate limit.

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

`lock.open` does not exist in the matrix and is rejected by design — opening a
latch is never available through IOWAP. A cluster task for a domain whose
exposure is not `on` fails with a clear deny reason in the node logs and the
`ha-exec` metrics.

## Security model

- HA core holds **no relay credentials** — the app container holds the only
  relay token (in `/data/.relay/`) and is the single bridge to the relay.
- `ha-exec` enforces the capability matrix: `domain`+`service` are never taken
  from the task payload, entity scope is validated per domain, and a
  per-capability rate limiter throttles runaway automations.
- Core→app communication is the official `hassio.app_stdin` channel only — no
  network ports are opened toward HA core. The app needs `hassio_role:
  manager` to call the HA core API through the Supervisor proxy.
- Safety automations stay **local**: never couple a safety behavior to the
  relay being up.

## Node status in HA

The app pushes its state into Home Assistant every `status_push_interval`
seconds (default 60) via the Supervisor proxy — HA core never polls the app:

- `binary_sensor.iowap_node_ready` — `on` while the node-daemon heartbeats
  healthily, otherwise `off` with a `reason` attribute. Attributes: `node_id`,
  `last_heartbeat`, `active_profile`, `capabilities`, `auth_loop`, `error`.
- `sensor.iowap_node_metrics` — state = number of published capabilities.
  Attributes: `tasks_completed`, `tasks_failed`, `in_flight`, `per_cap`
  (per-capability `calls`, `denied`, `last_call`, `last_outcome` counted by
  the `ha-exec` handler).

## Submitting tasks from Home Assistant

### Service: `iowap.submit_task`

Submits a single-stage task to the relay through the app's stdin channel.
The envelope is crash-safe buffered in `/data/outbox.jsonl` (fsync per line)
and drained by the app with retry — a relay outage at submit time loses
nothing. Unknown capabilities are rejected fail-fast when the app has a fresh
cluster view, and fail-open when the cache is empty (relay offline must not
silently drop tasks).

| Field | Required | Description |
|-------|----------|-------------|
| `capability` | yes | Capability to run, e.g. `agent.ai` |
| `payload` | yes | JSON payload for the capability stage (must satisfy its input schema) |
| `name` | no | Human-readable task name |
| `priority` | no | 1–9, lower = sooner (default 5) |

Example — ask the cluster agent when the doorbell rings:

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

> **Payload keys must match the capability's input schema.** For the built-in
> `ha.*` capabilities see the table above; for cluster capabilities (`agent.ai`
> etc.) check the relay dashboard or call `iowap.get_capabilities` as described
> below.

### Service: `iowap.get_capabilities`

Returns the capabilities the cluster currently offers (optionally with their
input schemas) — for scripting and automations via `response_variable`.

| Field | Default | Description |
|-------|---------|-------------|
| `include_schema` | `true` | Include each capability's `input_schema` |
| `available_only` | `false` | Only capabilities that currently have an available node |

### Blueprints

The integration generates one **automation blueprint** per published cluster
capability (plus a matching **script blueprint**) into
`blueprints/automation/iowap/` and `blueprints/script/iowap/`. They are
regenerated automatically when the cluster's capability list changes; each one
wraps `iowap.submit_task` with the capability's input schema as blueprint
inputs. Trigger and condition are optional inputs — leave them empty and wire
trigger/condition in the automation editor instead, or configure the whole
automation from the blueprint.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| App start fails: `ERROR: no relay_url configured` | Set `relay_url` in the app options |
| Node stuck `pending` in relay dashboard | Approve the node `ha-app-node` in the dashboard; the runtime token is minted on next refresh |
| Node never appears on the relay | Check `relay_url` reachability from the HA host and the app log (Settings → Apps → IOWAP Node → Log) |
| `iowap.submit_task` errors: unknown capability | The app's capability cache is stale — check relay connectivity; the next successful drain refreshes it |
| Tasks submitted but nothing happens | Check the outbox backlog: `ls -la /addon_configs/…` is app-internal; instead look at `sensor.iowap_node_metrics` (`per_cap.last_outcome`) and the app log for deny reasons |
| A domain denies every call | Its exposure mode is `readonly`/`off` — set it to `on` in the integration's Configure dialog |
| Rate-limit denies | Raise `rate_limit_per_min` in the app options (default 20/min per capability) |
| Blueprint missing for a capability | Blueprints regenerate on the next integration reload once the relay is reachable again |

## Related

- [Node framework](setup.md) — registering and running nodes on plain hosts
- [Token lifecycle](token-lifecycle.md) — what the `rt_`/`rs_` tokens in the app container mean
- [Capabilities](capabilities.md) — how capability schemas work cluster-side
- [iowap-ha repo](https://github.com/iowap-org/iowap-ha) — source