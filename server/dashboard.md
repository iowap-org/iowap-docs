# Dashboard

The web UI for managing nodes, users, tasks, and tokens:

```
http://<relay-host>:8788/relay/v2/dashboard/
```

## First login and bootstrap

Before any human user exists, the cluster is bootstrapped with the master
admin seed (created on the relay host — see
[server setup](setup.md), step 3):

1. Open the dashboard login page
2. Choose **Master seed**, paste the seed
3. You are redirected to **Create First Admin**
4. Enter a username (optional email) — the dashboard shows a generated
   temporary password; store it
5. Log out, log in as the new admin, change the password when prompted

Master-seed login auto-disables after the first human admin exists; the
bootstrap page only appears while no human admin exists.

## Human users and groups

For daily administration create human accounts (Users → New user): unique
username, ≥ 12-character password (bcrypt-stored), optional email, at
least one group. New users must change their password on first login.

| Group | Typical permissions |
|-------|---------------------|
| `admin` | Full access |
| `operator` | View dashboard, approve nodes |
| `readonly` | View only |

Permissions (editable per group under **Groups**): `dashboard:view`,
`nodes:approve`, `nodes:token`, `nodes:delete`, `users:manage`,
`groups:manage`.

Deactivate (no login, history stays), delete, or reset-password users from
the same view. The **last active admin** cannot be deleted unless recovery
mode is enabled.

## Node management

The **Nodes** view lists registered nodes with status, heartbeated
capabilities (may change at runtime), and last-seen. Actions:

- **Approve** a `pending` node (review role + capabilities) → the node gets
  a runtime token and starts claiming
- **New token** for a node whose token leaked or expired — invalidates the
  previous one
- **Delete** — removes the record, tokens, presence, routes, and claims

Status meanings and the auto-busy rules: [tasks and statuses](../concepts/tasks.md).

## Cluster overview and metrics

The home page shows node totals, task/stage statistics, recent artifacts,
and recent events. The built-in metrics page at
`/relay/v2/dashboard/metrics` renders the same data as the machine
endpoint: number cards (nodes, queue depth), bar charts (tasks/stages by
status), and auth-failure counters — self-refreshing. Machine-readable:
`/metrics` (Prometheus text, no auth) and
`/relay/v2/dashboard/api/metrics` — see [observability](../concepts/observability.md).

## Endpoints behind the UI

The dashboard is static HTML calling a JSON API — usable from scripts as
well (full table: [API reference](../reference/api.md)):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/relay/v2/dashboard/login` | Authenticate, set session cookie |
| POST | `/relay/v2/dashboard/api/bootstrap` | Create first admin (master seed only) |
| GET | `/relay/v2/dashboard/api/overview` | Cluster overview JSON |
| GET/POST | `/relay/v2/dashboard/api/users` | List / create users |
| POST | `/relay/v2/admin/nodes/{id}/approve` | Approve node |
| POST | `/relay/v2/admin/nodes/{id}/token` | Issue runtime token |
| DELETE | `/relay/v2/admin/nodes/{id}` | Delete node |

## Security best practices

- Master seed: password manager, never shared, never on worker nodes; on
  suspicion of leak — reset the database and re-bootstrap.
- One account per human; groups over individual permissions; deactivate
  leftovers.
- Node tokens: `chmod 600` on the node's token file; issue a new token if
  one leaked.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Cannot log in | No active admin / wrong password | Reset password or recovery mode ([admin](admin.md)) |
| Pending node never approved | Nobody clicked | Nodes → Approve |
| Node shows offline | Heartbeats missing | Restart the node daemon, check its token |
| User cannot approve | Missing permission | Group with `nodes:approve` |
| Lost master seed | Not recoverable | Delete DB, re-seed, re-bootstrap |
| Master-seed option missing | A human admin exists and recovery is off | Use the human admin or enable recovery |

## Related pages

- [admin](admin.md) — the same operations via API/CLI
- [server setup](setup.md) — installation
- [concept: tokens](../concepts/tokens.md) — credentials
- [glossary](../concepts/glossary.md) — terminology