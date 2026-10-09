# Server Administration

Operations by the human or agent that **runs the relay** — users, nodes,
recovery. Installation: [setup](setup.md). Dashboard UI:
[dashboard](dashboard.md).

## Node management

Every new node starts in `pending` and must be approved before it claims
work (node side: [node setup](../node/setup.md)).

### Approve a node

Dashboard: open **Nodes** → pending node → **Approve** → review role and
capabilities → **Confirm**.

API equivalent — an admin node (registered with the master seed through
the bootstrap flow) calls:

```bash
curl -H "Authorization: Bearer rt_..." \
  -X POST "http://<relay>:8788/relay/v2/admin/nodes/${NODE_ID}/approve" \
  -H "Content-Type: application/json" \
  -d '{"role":"service","capabilities":[{"name":"storage.archive.native","version":"1.0.0"}]}'
```

### Issue a new runtime token

```bash
curl -H "Authorization: Bearer rt_..." \
  -X POST "http://<relay>:8788/relay/v2/admin/nodes/${NODE_ID}/token"
```

Invalidates the node's previous runtime token. Alternatively the node
recovers itself via registration secret (`POST /relay/v2/auth/refresh`,
which rotates the secret — see [token operations](../node/tokens.md)).

### Delete a node

Dashboard **Nodes → Delete** (two-step confirm), or:

```bash
curl -H "Authorization: Bearer rt_..." \
  -X DELETE "http://<relay>:8788/relay/v2/admin/nodes/${NODE_ID}"
```

Removes the node record, all its tokens, presence data, route registry
entries, and claim references. The node must register again to return.

### Node statuses

| Status | Meaning | Set by |
|---|---|---|
| `pending` | Registered, not yet approved | relay on registration |
| `approved` | Approved, no heartbeat yet | relay on approval |
| `online` | Heartbeating, claiming | relay on heartbeat |
| `idle` / `busy` | Available / not claiming (runtime) | operator CLI or auto-busy |
| `maintenance` | Out of rotation | operator |
| `offline` | Heartbeat timeout exceeded | relay watchdog |

An approved node returning from `offline` needs **no re-approval** — the
heartbeat flips it back to `online`. Status model:
[tasks and statuses](../concepts/tasks.md).

## Recovery mode

If every human admin is locked out, re-open master-seed login from the
relay host:

```bash
# 1. Deactivate every human admin account (required):
relay-recovery --db-path ~/.relay/server.db enable-recovery --all

# 2. Restart the relay with master-seed login allowed:
RELAY_ENABLE_MASTER_SEED_LOGIN=true relay-server server --port 8788
```

3. Log in with the master seed, create a new admin, set its password.
4. Stop the relay, restart **without** the env var
   (`enable_master_seed_login: false`), re-activate the legitimate admin
   accounts in the dashboard.

**Why `--all` is required:** the relay refuses to start with
`RELAY_ENABLE_MASTER_SEED_LOGIN=true` while any human admin is still
active — a stolen master seed alone cannot silently hijack a running
cluster.

Lost the master seed itself? Not recoverable — stop the relay, delete the
database, re-seed, re-bootstrap (`enable-recovery` cannot resurrect an
unknown seed).

## Credential hygiene

- The master seed is root-equivalent: password manager, never scripts,
  never git.
- Runtime tokens live at node-side files (default `~/.relay/`), chmod 600.
- Master-seed login is unavailable in normal operation — recovery mode
  first.
- Rotating `session_secret` logs out every dashboard session.

## Verification

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  http://<relay>:8788/relay/v2/admin/nodes -H "Authorization: Bearer rt_..."
# -> 200 with a valid admin node token / 401 without
```

## Related pages

- [dashboard](dashboard.md) — the UI for all of the above
- [server setup](setup.md) — install, systemd, TLS
- [concept: tokens](../concepts/tokens.md) — credential families
- [API reference](../reference/api.md) — endpoint table