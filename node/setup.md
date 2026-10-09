# Node Setup

From a blank host to an online daemon claiming tasks. Prerequisites: the
relay URL, Python 3.11+, network reachability. Server side:
[server setup](../server/setup.md). Concepts: [nodes](../concepts/nodes.md).

## 1. Install

The node framework is its own repo — not part of iowap-server:

```bash
git clone https://github.com/iowap-org/iowap-node.git
cd iowap-node
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

```bash
node-cli --help | head -3
# -> usage: node-cli ...    (console script from [project.scripts])
```

No submodules, no server checkout needed — the CLI reads docs from the
relay at runtime (`node-cli docs`), not locally.

## 2. Point the node at the relay

Either pin the relay URL once (recommended for fixed installs):

```bash
node-cli relay set --server-url http://192.0.2.10:8788
```

…or let the node **discover** the relay over mDNS on every fallback
(works only when the server advertises — `enable_mdns: true` in the
server's config, and nothing strips mDNS on the LAN):

```bash
node-cli relay set --discover
node-cli relay discover --timeout 5
# -> http://192.0.2.10:8788
```

Discovery is name-filtered (service `IOWAP Relay Service`); other
`_http._tcp` broadcasts on the LAN are ignored. The pinned base_url can be
removed again with `--discover` (unpins from `relay_config.json` and the
state file).

## 3. Register

```bash
node-cli node register 192.0.2.10:8788        # host:port or URL
node-cli node register http://192.0.2.10:8788 --name my-node --json
# Re-registering an existing identity requires --force
```

Creates the state files itself (writes nothing on failure):

| File | Content |
|------|---------|
| `~/.relay/iowap-agent.json` | `node_id`, `node_name`, `registration_secret`, `capabilities`, `base_url` |
| `~/.relay/iowap-agent.token` | runtime token (JSON envelope with `expires_at`) |

Manual alternative for scripted setups:
`POST /relay/v2/auth/register` with
`{"node_name": …, "endpoint": null, "role": "node", "capabilities": […]}` —
exactly what `node register` does internally.

## 4. Wait for approval

The node is `pending` — an admin must activate it (dashboard **Nodes →
Approve**, or admin API: [server admin](../server/admin.md)). Poll the
status without a Bearer token:

```bash
curl -X POST "http://192.0.2.10:8788/relay/v2/auth/status" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "V34ETT74", "registration_secret": "rs_..."}'
# -> {"node_id": "V34ETT74", "status": "pending", ...}
```

Token recovery (after approval) is automatic in the daemon; the manual
flow is in [token operations](tokens.md).

## 5. Define capabilities

The daemon is **capability-agnostic** — everything is in YAML profiles.
Working profiles live in `~/.relay/profiles.d/`; the daemon reads only
`~/.relay/node.yaml`:

```bash
mkdir -p ~/.relay/profiles.d
cat > ~/.relay/profiles.d/default.yaml <<'YAML'
capabilities:
  - name: chat.ai
    version: "1.0.0"
    auto_publish: true
    claimable: true
    handler: /opt/relay/handlers/chat-ai.sh
    max_parallel: 2
    timeout: 300
YAML

node-cli capabilities validate default
# -> profile is valid
node-cli capabilities publish default      # atomic write to node.yaml
# -> published
```

Field reference: [capabilities how-to](capabilities.md); the model behind
it: [concept: capability](../concepts/capabilities.md).

## 6. Run the daemon

Two daemons exist — SSE-driven and polling; comparison and when to pick
which: [operations](operations.md). Foreground first, then as a service:

```bash
# Foreground (test)
node-cli daemon foreground
# or the standalone SSE daemon:
node-daemon --foreground

# Background (PID file + log under ~/.relay/):
node-cli daemon start
```

systemd user unit (example):

```ini
[Unit]
Description=IOWAP Node

[Service]
Environment=RELAY_BASE_URL=http://192.0.2.10:8788
UMask=0077
ExecStart=%h/iowap-node/.venv/bin/node-cli daemon foreground
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
mkdir -p ~/.config/systemd/user && cp unit-file ~/.config/systemd/user/iowap-node.service
systemctl --user daemon-reload && systemctl --user enable --now iowap-node.service
```

## Verification

```bash
node-cli heartbeat && node-cli status
# -> status file written; last heartbeat visible
cat ~/.relay/worker_status.json
# -> {"status": ..., "auth_loop": false, ...}
systemctl --user is-active iowap-node.service
# -> active
```

Dashboard: the node appears `online`. Submit a matching task — the node
claims and completes the stage.

Token files are credentials — the daemon does not set restrictive modes
automatically: `chmod 600 ~/.relay/iowap-agent.token ~/.relay/iowap-agent.json`
(`UMask=0077` in the unit achieves it permanently).

## Troubleshooting

| Problem | Solution |
|---|---|
| `401` on heartbeat | Token expired → daemon auto-refreshes; if lost, recover (see [token operations](tokens.md)) |
| `403` on claim | Capability not in the latest heartbeat — check profile + `auto_publish: true` |
| `404` on refresh | Wrong base_url, or the node was deleted — re-register |
| Node stays `pending` | Admin must approve (dashboard/admin API) |
| Node `offline` | Daemon down or heartbeat interval wrong — `systemctl --user status`, `tail ~/.relay/node-cli.log` |
| Both credentials expired | Re-register |
| Daemon exits under systemd | Absolute paths in `ExecStart`, `WorkingDirectory`, `User=` owning `~/.relay` |
| Daemon won't claim | No `claimable: true` capability or handler missing — `node-cli capabilities validate` |
| Handler timeout | Raise the profile's `timeout:` |
| mDNS unreachable | Pin `base_url` instead; check Avahi/reflector |

## Related pages

- [operations](operations.md) — daemon variants, status, maintenance
- [capabilities how-to](capabilities.md) — profiles in depth
- [token operations](tokens.md) — refresh and recovery
- [CLI reference](cli.md) — every command
- [integrations: Home Assistant](integrations/home-assistant.md) — HAOS app as a node