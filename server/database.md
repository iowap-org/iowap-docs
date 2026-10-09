# Server Database

Choosing and operating the relay's database backend. Architecture details
and "add your own backend": [reference/database-backends.md](../reference/database-backends.md).

## What it is

The relay stores all state — nodes, tasks, stages, tokens, RBAC, audit
logs — in a relational database. The layer is built on **SQLAlchemy Core**
(not an ORM): the same code runs unchanged on SQLite and PostgreSQL; the
active backend is a single config field (`db_type`).

| Backend | Config value | Driver / extra | Status |
|---------|-------------|----------------|--------|
| SQLite | `sqlite` | stdlib `sqlite3` | default, fully implemented |
| PostgreSQL | `postgres` | `psycopg` (`pip install ".[postgres]"`) | implemented |

## Choosing

```yaml
# ~/.relay/config.yaml — SQLite (default), nothing to configure:
db_type: sqlite
db_path: ~/.relay/server.db
```

```yaml
# ~/.relay/config.yaml — PostgreSQL:
db_type: postgres
pg_dsn: postgresql+psycopg://user:pass@host:5432/relay
```

```bash
pip install ".[postgres]"   # driver extra for PostgreSQL
```

The DSN host can be any reachable address (IP, DNS name, overlay name);
`pool_pre_ping` recycles stale pool connections automatically. In Docker
compositions the bundled/postgres-service variant is described in
[docker](docker.md).

Switching an existing deployment from SQLite to PostgreSQL is **not a
migration** — start a fresh PostgreSQL database and let the relay build the
schema; task/node history does not carry over automatically.

## Operating

- **Migrations** run automatically on startup — additive, versioned, no
  downtime, no manual steps. A database without a ledger row replays the
  (idempotent) history; one ahead of the running code is left untouched.
- **Backups:** single-file hot backup (WAL allows online copies):
  ```bash
  sqlite3 ~/.relay/server.db ".backup ~/.relay/backup/server-$(date +%F).db"
  ```
- **Corrupt DB:** restore the newest backup and restart — the migration
  runner brings the schema forward.

## Verification

```bash
curl -s http://localhost:8788/ready
# -> {"status":"ready","database":true,...}
```

A wrong DSN or unreachable PostgreSQL appears as
`"database": false` and `status: degraded` on `/ready`, with the engine
error in the server journal.

## What it is NOT

- **Not sharded** — one relay process owns the database; do not point
  multiple relay instances at one `server.db`.
- **Not a migration tool between backends** — switching means a fresh
  start (see above).

## Related pages

- [server setup](setup.md) — install, backups schedule
- [Docker](docker.md) — bundled Postgres composition
- [reference: database backends](../reference/database-backends.md) — layer internals, adding a backend