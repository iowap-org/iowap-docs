# Storage Node on QNAP Container Station

Deploy the storage node on a QNAP NAS (x86_64, Container Station). It
stores files, manages backups, and transfers folders — the cluster's
central storage. Architecture: [storage](storage.md).

## Prerequisites

- QNAP with **Container Station** (QTS/QuTS hero), x86_64 CPU
- A running relay server (same LAN or overlay network)

## 1. Load the image

```bash
docker pull ghcr.io/iowap-org/iowap-storage:latest
```

## 2. Start the node

**Via `docker run` (SSH):**

> Always pass `-v iowap-storage-state:/home/appuser/.relay` — Container
> Station does not create it automatically. Without that volume the node
> loses its identity (node_id + token) on every restart and re-registers.

```bash
docker run -d \
  --name iowap-storage \
  --restart unless-stopped \
  -e RELAY_URL=http://192.0.2.60:8788 \
  -e NODE_NAME=storage-node \
  -v /share/Container/iowap-storage:/storage \
  -v iowap-storage-state:/home/appuser/.relay \
  ghcr.io/iowap-org/iowap-storage:latest
```

**Via Container Station (GUI):** Overview → Create → Image →
`ghcr.io/iowap-org/iowap-storage:latest`, set the env vars (table below),
bind-mount `/storage` to a NAS folder, **create the named volume** for
`/home/appuser/.relay`, start.

## 3. Approve the node

It registers as `pending` — approve in the relay dashboard
(**Nodes → Approve**) or via the admin API
([server admin](../server/admin.md)).

## Configuration

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `RELAY_URL` | no* | mDNS discovery | Relay URL. *If unset, the node finds the relay via mDNS on the LAN — relay and node must be on the same network. |
| `NODE_NAME` | no | hostname | Dashboard display name |
| `NODE_ENDPOINT` | no | auto (own IP + bridge port) | Only set if the relay cannot reach the node directly |
| `NODE_REGISTRATION_SECRET` | no | — | Pre-created `rs_…` secret for headless registration |
| `RELAY_SERVER_IP` | no | *(from RELAY_URL)* | Explicit bridge-allowlist override — practically never needed |
| `RELAY_STORAGE_PATH` | no | `/storage` | Storage root (set by the image) |

The bridge allowlist resolves the relay IP automatically from
`RELAY_URL` (or mDNS) — everything works without manual IP pins in normal
operation.

## Volumes

| Mount | Purpose |
|-------|---------|
| `/storage` | NAS export — files + backups. Bind-mount to a QNAP folder. |
| `/home/appuser/.relay` | Node meta + token — **named volume** (persists identity). Never recreate the container without it. |

## Verification

```bash
docker logs iowap-storage 2>&1 | grep -i "register\|heartbeat" | tail -3
# -> registration + heartbeat lines
curl http://192.0.2.60:8788/relay/v2/docs 2>/dev/null >/dev/null
# relay is up; node appears in the dashboard once approved
```

A stored file lands under the QNAP folder you bound to `/storage`
(`files/…`, `backups/…` namespace the tree).

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `Connection refused` on start | Relay unreachable — check `RELAY_URL` / relay running |
| Node stays `pending` | Approve in the dashboard |
| Bridge routes dead | Set `RELAY_SERVER_IP` explicitly when the QNAP cannot resolve the relay via DNS |
| Files don't land on the NAS | `/storage` must bind-mount a real QNAP folder |
| Node re-registers after restart | The state volume is missing — see the warning above |

## Source

Python code: [iowap-org/iowap-storage](https://github.com/iowap-org/iowap-storage);
images built from [iowap-org/iowap-docker](https://github.com/iowap-org/iowap-docker).