# Docker Deployment

Run the relay as a container. Compose files live in the
[iowap-docker](https://github.com/iowap-org/iowap-docker) repo (server
compose under `server/`); a pre-built image is on GHCR. Source install:
[server setup](setup.md).

## Quick start (SQLite — default)

```bash
git clone https://github.com/iowap-org/iowap-docker.git
cd iowap-docker

# 1. Create your environment (generate real secrets!)
docker/server/.env.example | cp -  .env
#    edit .env: RELAY_MASTER_SEED, RELAY_SESSION_SECRET,
#    RELAY_SESSION_COOKIE_SECURE=false (plain http on LAN)

# 2. Build & start
docker compose -f server/docker-compose.yml up -d --build

# 3. Open the dashboard and log in with your master seed
#    http://<host>:8788
```

SQLite is the default backend; the DB, artifacts, and config live in the
named volume `relay-data` and survive `docker compose down` and rebuilds.
Only `docker compose down -v` removes them — the master seed lives in the
database, so losing the volume loses the credential.

## Pull instead of build

```bash
docker volume create relay-data
docker run -d \
  --name iowap-server \
  --restart unless-stopped \
  -p 8788:8788 \
  -e RELAY_MASTER_SEED="$(openssl rand -hex 24)" \
  -e RELAY_SESSION_SECRET="$(openssl rand -base64 32)" \
  -e RELAY_SESSION_COOKIE_SECURE=false \
  -v relay-data:/app/.relay \
  ghcr.io/iowap-org/iowap-server:latest
```

Without `RELAY_MASTER_SEED` the entrypoint generates a random seed and
prints it to the container log on first start. The entrypoint runs DB
init + seed apply, then starts uvicorn on `:8788`.

## Database backends

| Backend | How to enable | When |
|---|---|---|
| SQLite (default) | nothing | single relay, simplest |
| PostgreSQL | `--profile postgres` or external DSN | shared/larger setups |

**PostgreSQL, two ways** — in both the relay only needs
`RELAY_DB_TYPE=postgres` + `RELAY_PG_DSN`:

```bash
# Option A: external database on another host — just the DSN:
#   RELAY_PG_DSN=postgresql+psycopg://relay:<pw>@192.0.2.50:5432/relay
docker compose -f server/docker-compose.yml up -d --build

# Option B: bundled postgres container:
#   RELAY_PG_DSN=postgresql+psycopg://relay:<pw>@postgres:5432/relay
#   POSTGRES_USER=relay  POSTGRES_PASSWORD=<pw>  POSTGRES_DB=relay
docker compose -f server/docker-compose.yml --profile postgres up -d --build
```

The `POSTGRES_*` variables configure only the bundled container —
irrelevant for an external DB. Details and pitfalls: [server
database](database.md).

## TLS (HTTPS)

The relay serves HTTPS when both cert files are set; certs are mounted
read-only at `/certs`:

```dotenv
RELAY_TLS_CERTS_DIR=./certs
RELAY_TLS_CERTFILE=/certs/fullchain.pem
RELAY_TLS_KEYFILE=/certs/privkey.pem
```

Leave the vars empty for plain HTTP; the healthcheck tries `http` then
`https`, so it works either way. With HTTPS keep
`RELAY_SESSION_COOKIE_SECURE=true` (default).

## Environment reference

| Variable | Default | Purpose |
|---|---|---|
| `RELAY_MASTER_SEED` | *(random)* | Master admin seed, applied on first start |
| `RELAY_DB_TYPE` | `sqlite` | `sqlite` or `postgres` |
| `RELAY_PG_DSN` | *(empty)* | Postgres DSN (`postgresql+psycopg://…`) |
| `RELAY_SESSION_SECRET` | *(empty)* | Signs dashboard sessions (≥ 32 chars) |
| `RELAY_SESSION_COOKIE_SECURE` | `true` | `false` for plain HTTP on LAN |
| `POSTGRES_USER`/`_PASSWORD`/`_DB` | `relay` | Bundled postgres container credentials |

## Image notes

- Multi-stage build; runtime `python:3.11-slim`, `tini` as PID 1, non-root
  appuser (overridable: `--build-arg PUID=1000 --build-arg PGID=1000` for
  NAS bind mounts).
- `psycopg[binary]` is included — both backends work out of the box.
- Build context is the repo root (`server/Dockerfile`), so tag pinning via
  `IOWAP_SERVER_REF` (default `main`) works.

## Verification

```bash
docker compose -f server/docker-compose.yml ps
# -> iowap-server   ...  (healthy)     # /health-responder
docker compose -f server/docker-compose.yml logs relay | head
# -> entrypoint: seed created / already exists, uvicorn startup
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `master seed already exists` in log | DB already has a seed | normal on restart — login unchanged |
| Relay fails fast on start | DSN/password mismatch (Option B) | `RELAY_PG_DSN` + `POSTGRES_PASSWORD` must carry the same password |
| `postgres://` DSN rejected | dialect missing | use `postgresql+psycopg://` |
| DSN host unreachable (Option B) | `localhost` points at the relay container | use `postgres` (compose network name) |
| Lost admin access | volume deleted | restore `relay-data` or re-bootstrap with a fresh volume |