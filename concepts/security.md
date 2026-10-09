# Security Model

This page answers: what are the security boundaries of an IOWAP cluster?

## What it is

IOWAP is designed for **private networks** (homelab, Tailscale/WireGuard
overlays). The boundaries:

- **The core routes by capability string.** It does not choose tools,
  models, or parameters, so it cannot be tricked into running untrusted
  logic — it never interprets payloads.
- **One runtime token per node, prefix-scoped credential families**
  (see [tokens](tokens.md)). Refreshing invalidates the previous token;
  the master seed never travels over HTTP.
- **Nodes run with minimal privileges** and only touch the paths and
  devices they own. The node daemon runs as a user systemd unit.
- **Nodes with reasoning validate destructive payloads** before they act;
  nodes without reasoning (`.native`) cannot improvise — they only do
  what the stage says (see [tasks](tasks.md) for the decision rules).
- **Unknown capabilities are ignored** — a node cannot claim work outside
  the capability set it heartbeats (exact match).
- **File-serving nodes are fail-closed**: the daemon's ephemeral
  file-serve endpoint binds only where configured
  (`IOWAP_SERVE_HOST`) and accepts downloads only from source IPs on its
  allowlist (`IOWAP_SERVE_ALLOW`, plus the relay's IP — resolved from
  `RELAY_URL`); without the relay IP in the allowlist, LAN peers are
  refused with 403.
- **Dynamic node routes are proxy-validated**: upstreams must point at the
  node's own registered endpoint origin or a configured allowlist host;
  loopback, link-local and cloud-metadata targets are refused (fail-closed,
  HTTP 502) — the relay cannot be turned into an open proxy into its own
  network.
- **Keep the relay behind your firewall.** Auth-failure counters are
  exported on `/metrics`; protected routes answer 401 without a valid
  token.

Expired tokens are purged hourly (maintenance watchdog).

## How it works

The enforcement points, in one list:

| Layer | Mechanism |
|-------|-----------|
| Node ↔ relay | Bearer `rt_` token on every mutating call; 401 gate |
| Dashboard | Signed session cookie (bcrypt-backed user store) |
| Registration | No port-opening: nodes register and heartbeat outbound only |
| Node file serve | Source-IP allowlist, deliberate bind host, fail-closed |
| Dynamic routes | Upstream allowlist + endpoint-origin check, no `DELETE` proxy |
| Scheduler | Exact capability match; `available`/`busy` claim gates |
| Artifacts | Watchdog-purged transient store, no durable relay-side copies |

## What it is NOT

- **Not an internet-facing service** — there is no rate limiting beyond
  auth-failure observability, no WAF, no TLS termination built in (put a
  reverse proxy in front if you need HTTPS — see
  [server setup](../server/setup.md)).
- **Not a sandbox** — handlers run as the node's user with that user's
  filesystem rights; pick handlers accordingly.
- **Not end-to-end encrypted** — traffic node↔relay is unencrypted HTTP
  within your network unless you add TLS at a proxy layer; for untrusted
  networks run everything inside a WireGuard/overlay network first.

## Related pages

- [tokens](tokens.md) — credential families and TTLs
- [node security setup](../node/setup.md) — token files and allowlists
- [server setup security notes](../server/setup.md) — TLS and admin bootstrap
- [glossary](glossary.md) — verbatim terminology