# Database Backends — Reference

Internal reference for the database layer: how the multi-backend
abstraction is built and how to add a backend. Operational choosing and
backup: [server/database.md](../server/database.md).

## Layer design

The layer is built on **SQLAlchemy Core** (expressions + `text()`, not the
ORM): every query goes through a database-independent expression, so the
same code runs unchanged on SQLite and PostgreSQL. Business logic (auth,
scheduler, API, dashboard) never touches the driver directly — it calls
`db.get_conn()` and receives a SQLAlchemy `Connection`.

| Backend | Config value | Driver / extra | Status |
|---------|-------------|----------------|--------|
| SQLite | `sqlite` | stdlib `sqlite3` | default |
| PostgreSQL | `postgres` | `psycopg` (`pip install ".[postgres]"`) | implemented |

## What the abstraction consists of

- **Schema** — declared once as portable `sa.Table` objects in
  `core/tables.py`; `metadata.create_all(engine)` builds it on any
  backend.
- **Queries** — the `q(sql, params)` helper in `core/db.py` rewrites
  `?`-positional SQL into named bind parameters; SQLAlchemy renders the
  correct placeholder per dialect (`?` SQLite, `$N` PostgreSQL). The
  legacy call shape `conn.execute(q("… WHERE id = ?", (id,)))` is
  preserved everywhere.
- **Row access** — a small shim on SQLAlchemy's `Row` forwards
  `row["col"]` to `row._mapping[col]`, so string-subscript code is
  unchanged.
- **Migrations** — `MIGRATIONS` in `core/db.py` is the ordered history of
  `(version, name, apply_fn)` steps recorded in the `schema_version`
  table. An unknown database replays the (idempotent) history and stamps
  itself; one ahead of the running code is left untouched. Bodies are
  backend-aware (`PRAGMA table_info` vs `information_schema`).
- **Timestamps** stay ISO-8601 TEXT strings — the existing SQLite file
  stays byte-identical.

## Adding a new backend

Exactly three things:

1. **Driver extra** in `pyproject.toml`:

```toml
[project.optional-dependencies]
cockroach = ["psycopg[binary]>=3.1"]
```

2. **Backend class** — `relay_server/core/db_cockroach.py`, mirroring
`db_postgres.py`:

```python
"""CockroachDB backend for the relay server."""
import sqlalchemy as sa
from relay_server.core import tables
from relay_server.core.db import Database, _run_migrations, _seed_default_rbac


class CockroachDatabase(Database):
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = sa.create_engine(self._dsn, pool_pre_ping=True, future=True)
        return self._engine

    def get_conn(self):
        return self._get_engine().connect()

    def init_db(self):
        with self._get_engine().begin() as conn:
            tables.metadata.create_all(conn)
            _seed_default_rbac(conn)
            _run_migrations(conn)

    def close(self):
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
```

3. **Factory entry + config field** — in `create_database()`
(`core/db.py`):

```python
elif db_type == "cockroach":
    from relay_server.core.db_cockroach import CockroachDatabase
    return CockroachDatabase(settings.cockroach_dsn)
```

…plus `cockroach_dsn: str = ""` in `config.py`:

```yaml
# config.yaml
db_type: cockroach
cockroach_dsn: postgresql+psycopg://user:pass@host:26257/relay?sslmode=require
```

## Testing a new backend

```bash
# 1. No regressions against SQLite:
.venv/bin/python -m pytest tests/ -x -q
# 2. The on-disk invariant (existing SQLite DB stays intact):
.venv/bin/python -m pytest tests/test_db_backcompat.py -x -q
# 3. End-to-end with the new backend: register, heartbeat, schedule, dashboard.
```

## Design notes

- **No ORM** — full SQL control, dialect portability via Core.
- **`q()` helper, not a query builder** — legacy `?`-SQL preserved; new
  code may use full `sa.select()`/`sa.insert()` constructs.
- **Sync interface** — the engine pool is sync; async routes run DB calls
  in the threadpool (Starlette standard sync support).
- **Shared schema** — one `tables.metadata`; the legacy raw-DDL path is
  kept for SQLite so existing databases initialise byte-identically.
- **SQLite stays default** — PostgreSQL opt-in, no migration step for
  existing deployments.

## Related pages

- [server/database.md](../server/database.md) — choosing, backups, readiness
- [overview](../concepts/overview.md) — the system this sustains