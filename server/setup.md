# Server Setup

From zero to a running relay. Covers install, bootstrap, systemd, TLS, and
maintenance. Node side: [node setup](../node/setup.md). Container-first
path: [Docker](docker.md).

## What you get

- A central relay that routes tasks between nodes (concepts:
  [overview](../concepts/overview.md))
- A web dashboard at `http://<relay-host>:8788/relay/v2/dashboard/`
- Optional mDNS advertisement so nodes can find the relay as `iowap.local`

Requirements: a Linux host (small server, NAS, or always-on PC), Python
3.11+, LAN or overlay-network access.

## 1. Install from source

```bash
git clone --recursive https://github.com/iowap-org/iowap-server.git
cd iowap-server
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

```bash
relay-server --version
# -> version is printed; the console scripts relay-server and relay-recovery exist
```

> The `--recursive` flag matters: `docs/` is a git submodule pointing at
> [iowap-org/iowap-docs](https://github.com/iowap-org/iowap-docs). The relay
> serves it at `/relay/v2/docs/` — that is what `node-cli docs` reads. Left
> it out? `git submodule update --init`.

## 2. Configure the session secret

The relay signs dashboard session cookies with a persistent random string
(≥ 32 chars). **Without it the server refuses to boot.**

```bash
mkdir -p ~/.relay
echo 'session_secret: "<paste $(openssl rand -base64 32)>"' > ~/.relay/config.yaml
```

Keep it stable: rotating it invalidates every dashboard session (each admin
must log in again). Rotating is for suspected compromise only.

## 3. Create the master admin seed

```bash
relay-server admin init-master
# -> adm_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Store the printed `adm_…` seed in a password manager — it is shown once. It
is the emergency/bootstrap credential, never day-to-day auth.

## 4. Start the relay

```bash
# With mDNS (nodes can resolve iowap.local) — off by default:
RELAY_ENABLE_MDNS=true relay-server server --port 8788

# Or plain:
relay-server server --port 8788
```

```bash
curl http://localhost:8788/health
# -> {"status":"ok","version":"...","mode":"core","event_subscribers":8}
```

## 5. Bootstrap the first human admin

1. Open `http://<relay-host>:8788/relay/v2/dashboard/`
2. Choose **Master seed**, paste the seed
3. Create the first admin (username + generated temporary password)
4. Log out, log in as the new admin, change the password when prompted

Master-seed login is automatically disabled once a human admin exists.
Day-to-day work happens with human accounts — see
[dashboard](dashboard.md) and [admin](admin.md).

## 6. Systemd service

`/etc/systemd/system/iowap.service` (adjust paths and user):

```ini
[Unit]
Description=IOWAP Relay
After=network.target

[Service]
Type=simple
User=felix
WorkingDirectory=/home/felix/projects/iowap-server
ExecStart=/home/felix/projects/iowap-server/.venv/bin/relay-server server --port 8788
Environment=RELAY_ENABLE_MDNS=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now iowap.service
systemctl is-active iowap.service
# -> active
```

Update later: `git pull` + `pip install -e .` (only when dependencies
changed) + `sudo systemctl restart iowap.service`.

## 7. HTTPS / TLS

For a Homelab behind Tailscale/WireGuard, plain HTTP is the default posture.
Two options when you need TLS:

**Option A — native TLS:** set both files in `~/.relay/config.yaml`; the
relay serves HTTPS itself and stops advertising mDNS (TLS implies Internet
mode, mDNS is a LAN mechanism):

```yaml
# ~/.relay/config.yaml
tls_certfile: /etc/certs/iowap/fullchain.pem
tls_keyfile:  /etc/certs/iowap/privkey.pem
```

**Option B — reverse proxy:** terminate TLS outside, proxy to `:8788`. For
SSE clients disable proxy buffering and allow long read timeouts; set the
body limit above `max_upload_bytes` (100 MiB) or uploads will be rejected
by the proxy before the relay sees them.

```caddyfile
# /etc/caddy/Caddyfile — automatic Let's Encrypt
iowap.example.com {
    reverse_proxy 127.0.0.1:8788
}
```

```nginx
# nginx variant (certbot -d iowap.example.com)
server {
    listen 443 ssl http2;
    server_name iowap.example.com;
    ssl_certificate     /etc/letsencrypt/live/iowap.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iowap.example.com/privkey.pem;
    client_max_body_size 110m;      # > max_upload_bytes + multipart overhead
    location / {
        proxy_pass http://127.0.0.1:8788;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_buffering off;        # SSE
        proxy_read_timeout 24h;     # SSE
    }
}
```

Nodes behind a private CA: set `tls_ca_cert` in the node's
`relay_config.json` so the node trusts the relay certificate.

## 8. Database and backups

SQLite (WAL) is the default — single file at `~/.relay/server.db`, no
external database. PostgreSQL is an opt-in backend (see
[database](database.md)). Migrations run automatically on startup.

```bash
# Hot backup (online, transaction-consistent; WAL allows concurrent reads):
sqlite3 ~/.relay/server.db ".backup ~/.relay/backup/server-$(date +%F).db"
```

```cron
# every night at 03:00 (escape % in crontab)
0 3 * * *  sqlite3 ~/.relay/server.db ".backup ~/.relay/backup/server-$(date +\%F).db"
```

A corrupt DB (rare with WAL): restore the newest backup and restart — the
migration runner brings the schema forward.

## 9. Configuration reference

Set via `~/.relay/config.yaml` or `RELAY_`-prefixed environment variables
(env first, then YAML, explicit CLI flags override everything). Common
fields:

```yaml
# ~/.relay/config.yaml — common options
host: "0.0.0.0"
port: 8788
log_level: "info"                  # debug | info | warning | error
enable_mdns: false                 # true advertises iowap.local

tls_certfile: null                 # both set → HTTPS mode
tls_keyfile: null

db_path: "~/.relay/server.db"
artifacts_dir: "~/.relay/artifacts"

token_ttl_hours: 168               # runtime token TTL (7 days)
registration_secret_ttl_hours: 168 # recovery credential TTL (7 days)
claim_ttl_seconds: 60              # 60–300, dashboard-editable, live effect
heartbeat_interval_seconds: 10
heartbeat_timeout_multiplier: 5    # offline after 5 × interval silent

session_secret: "<random 32+ chars>"
session_cookie_secure: true        # false only for plain-HTTP LAN
enable_master_seed_login: false    # recovery mode only

max_upload_bytes: 104857600        # 100 MiB, single upload
max_payload_bytes: 10485760        # 10 MiB, task payload
max_chunk_size: 10485760           # 10 MiB, per chunked-upload chunk
max_inline_bytes: 5242880          # transfer ladder: inline bound (5 MB)
max_artifact_bytes: 52428800       # artifact bound (50 MB), above = bridge
max_retries: 2                     # per-stage retry budget (0–10)
```

## Verification

```bash
curl -s http://localhost:8788/health | grep -o '"status":"ok"'
# -> ok
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8788/relay/v2/discovery/heartbeat
# -> 401  (auth gate — correct: the route exists, token missing)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Boot refuses: session secret | Set `session_secret` (≥ 32 chars) in config.yaml or via env — see §2 |
| `iowap.local` not found | Use the relay IP; check Avahi on the relay host / mDNS reflector on the router |
| Port 8788 in use | `ss -lntp | grep 8788`, stop the other process, restart |
| Node stays `pending` | Approve in dashboard / admin API (see [admin](admin.md)) |
| `database is locked` | Another relay process on the same DB file — stop duplicates |
| `no such table` | Migration did not run — backup the DB, restart, runner fires |
| Proxy rejects uploads (413) | Raise proxy body limit above `max_upload_bytes` |
| SSE dead through proxy | `proxy_buffering off` + long read timeout |
| Firewall blocks nodes | Open TCP 8788 on the relay (mDNS needs UDP 5353) |

Security notes: the master seed is root-equivalent; tokens live under
`~/.relay/`; never commit either; the relay is a private-network service
(boundary model: [security](../concepts/security.md)).