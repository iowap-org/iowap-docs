# captures/ — real relay output as documentation source

CONTRIBUTING.md: **"Values come from real captures, never invented."** This
directory is where those real values come from. Every `# ->` expected-output
comment in the docs should be traceable to (or regenerable via) one of these
files.

## How to re-capture

On a machine with node-cli and a logged-in node state (`~/.relay/*`):

```bash
python3 tools/capture.py             # health, node list, capabilities
python3 tools/capture.py --metrics   # + relay metrics (long)
# -> captures/health-YYYYMMDD.md, captures/nodes-YYYYMMDD.md, ...
```

The relay is only asked read-only list/probe questions. The target relay is
whatever `node-cli` is pinned to (mDNS / `node-cli relay` / `~/.relay/`).

## What the script does

- Runs `node-cli server health` (covers `/health` + `/ready`), \
  `node-cli node list`, `node-cli capabilities server`, optionally \
  `node-cli server metrics`.
- Anonymizes the output before storing (`tools/_anonymize.py`).
- Stamps provenance into the file: UTC timestamp, exact command, policy note.

## Anonymization policy

| What | Rule |
|------|------|
| IPv4 addresses | Mapped deterministically to `192.0.2.1..N` (RFC 5737 TEST-NET-1) — first-appearance order, so re-captures stay stable |
| Relay tokens (`rt_`, `rs_`, `adm_`) | Cut to ellipsis form (`rt_…`) |
| Own/community domains | `example.com` |
| Node ids (short codes like `AMKJA9AE`) | Keep — they are capability identifiers, not credentials |

## CI tripwire

`tools/check_captures.py` runs in docs CI and enforces the same rules over
**all** Markdown (docs pages and captures): documentation-safe IPs only,
no full token shapes, no own domains. A failed rule = red PR. If a genuinely
needed address trips the check, anonymize the source, never allowlist it.