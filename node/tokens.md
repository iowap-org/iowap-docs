# Token Operations (Node Side)

Refresh, recovery, and the local credential files. The model behind the
families: [concept: tokens](../concepts/tokens.md).

## The local files

| File | Content |
|------|---------|
| `~/.relay/iowap-agent.json` | State file: `node_id`, `node_name`, `registration_secret` (`rs_…`), `capabilities`, `base_url` pin |
| `~/.relay/iowap-agent.token` | Runtime token (`rt_…`) as JSON envelope `{token, expires_at}` — rotated without touching the state file |

Both are credentials (anyone who reads them impersonates the node):
`chmod 600` both files, `chmod 700 ~/.relay`. Legacy plaintext token files
are migrated to the envelope on the next refresh automatically.

## Check lifetimes (read-only)

```bash
node-cli status
# -> local view incl. token expiry and last heartbeat
python3 -c "import json;print(json.load(open('$HOME/.relay/iowap-agent.token'))['expires_at'])"
# -> 2026-10-16T12:00:00+00:00
```

## Manual refresh (runtime token)

```bash
curl -X POST "http://192.0.2.10:8788/relay/v2/auth/refresh" \
  -H "Authorization: Bearer rt_..." \
  -H "Content-Type: application/json" \
  -d '{"requested_credential": "runtime_token"}'
```

Save the new token immediately — the old one is invalidated the moment the
new one is issued. The running daemon refreshes proactively (6-day
interval + expiry-margin rule), so manual refresh matters only for
one-shot CLIs on nodes without a daemon.

## Manual refresh (registration secret)

```bash
curl -X POST "http://192.0.2.10:8788/relay/v2/auth/refresh" \
  -H "Authorization: Bearer rt_..." \
  -H "Content-Type: application/json" \
  -d '{"requested_credential": "registration_secret"}'
```

## Recover a lost runtime token

Only `POST /relay/v2/auth/refresh` creates or rotates credentials;
`/auth/status` only reports lifetimes. Recovery needs `node_id` +
registration secret (no Bearer):

```bash
curl -X POST "http://192.0.2.10:8788/relay/v2/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "V34ETT74",
    "registration_secret": "rs_...",
    "requested_credential": "runtime_token"
  }'
```

The response carries a **new runtime token and a new registration secret**
— recovery rotates the secret. Persist both immediately:

```bash
jq -c '{token: .token, expires_at: .expires_at}' /tmp/refresh.json > ~/.relay/iowap-agent.token
jq -r .registration_secret /tmp/refresh.json
# -> paste into ~/.relay/iowap-agent.json (registration_secret key)
```

Both credentials expired? Re-register:
[node setup, step 3](setup.md). Re-registering a live identity without
`--force` returns 409 Conflict — recover instead.

## What it is NOT

- **Not a renewal service** — nothing refreshes a token after final
  expiry; the daemon's job is to always being *ahead* of expiry.
- **Not transferable** — a runtime token is bound to its `node_id`; don't
  copy tokens between nodes.

## Related pages

- [operations](operations.md) — the automatic maintenance intervals
- [setup](setup.md) — registration and file creation
- [concept: tokens](../concepts/tokens.md) — the four families
- [glossary](../concepts/glossary.md) — terminology