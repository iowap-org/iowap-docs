# Tokens

This page answers: which credentials exist in an IOWAP cluster, what are
they for, and how do they expire?

## What it is

The relay authenticates nodes and admins with four token families,
distinguished by their prefixes. Human dashboard users do not use tokens —
they log in with username/password and get a signed session cookie.

| Prefix | Name | Default TTL | Purpose |
|---|---|---|---|
| `adm_…` | Master admin seed | Until rotated | Bootstrap the cluster and recover admin access — emergency only |
| `rs_…` | Registration secret | 168 h (7 days, config `registration_secret_ttl_hours`) | Recovery only — recover a runtime token |
| `tp_…` | Temporary token | 24 h | Issued on registration, replaced after approval |
| `rt_…` | Runtime token | 168 h (7 days, config `token_ttl_hours`) | Day-to-day Bearer auth: heartbeat, claim, complete |

The initial `rs_` TTL is issued alongside registration and re-issued (fresh
window) whenever it is used for recovery.

## How it works

```
[Register] → temporary token (24 h) + registration secret (7 days)
       ↓
[Admin approves] → runtime token (7 days), node status: approved
       ↓
[Heartbeat] → status online → claim → work → complete
       ↓
[Before expiry] → POST /relay/v2/auth/refresh → new runtime token
       ↓
[Lost runtime token] → POST /relay/v2/auth/refresh with registration_secret
                     → new runtime token + new registration secret
```

- **One runtime token per node** — refreshing invalidates the previous one.
- **The registration secret is recovery only** — it is not usable for
  day-to-day auth and is rotated whenever it recovers a runtime token.
- **The master admin seed is emergency only** — it enables a bootstrap
  dashboard session while no human admin exists (or when master-seed login
  is explicitly enabled). It is created **on the relay host**; the HTTP API
  has no endpoint to initialise it, so a network attacker cannot claim the
  cluster root key. It is stored as a bcrypt hash; the plain seed is never
  kept on disk.
- **Expired tokens are purged hourly** by the maintenance token-cleanup
  watchdog.

Node-side operations (refresh, recovery, the local state file) are
documented in [node token operations](../node/tokens.md).

## What it is NOT

- **Not a shared secret** — every credential is single-credential per role;
  nodes never see each other's tokens.
- **Not an OAuth flow** — no third-party identity, no scopes; the dashboard
  session cookie is the only human path.
- **Not revocable mid-flight** — token invalidation happens by refresh
  (runtime), rotation (registration secret), or expiry (purge watchdog);
  there is no per-token revocation list.

## Related pages

- [node token operations](../node/tokens.md) — refresh/recover procedures
- [security](security.md) — boundary model
- [API auth endpoints](../reference/api.md) — register/refresh/status
- [glossary](glossary.md) — verbatim terminology