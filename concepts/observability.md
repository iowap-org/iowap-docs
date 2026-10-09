# Observability

This page answers: how do I watch a relay cluster — metrics, readiness,
logs?

## What it is

Three built-in surfaces, all dependency-free (no Prometheus server, no
Grafana required):

- **`/metrics`** (root, no auth) — Prometheus exposition text: in-process
  counters (`relay_auth_failures_total{endpoint="…"}`) and DB-derived
  gauges (`relay_nodes_total`, `relay_nodes_online`,
  `relay_queue_depth`, `relay_tasks{status="…"}`,
  `relay_stages{status="…"}`). A Prometheus server can scrape it without
  code changes.
- **`/ready`** (root, no auth) — readiness probe: database round-trip,
  maintenance-loop age, and last-sweep outcome
  (`{"status": "ready"|"degraded", "database", "scheduler",
  "maintenance_age_seconds", "maintenance_last_ok"}`). A sweep with any
  errored task flips `maintenance_last_ok` and degrades readiness.
- **Metrics dashboard** at `/relay/v2/dashboard/metrics` (session auth) —
  the same data as cards and bar charts; JSON backing:
  `/relay/v2/dashboard/api/metrics`.

Plus **structured logs**: one JSON object per line (`ts`, `level`,
`logger`, `msg`, `trace_id`). A middleware stamps a per-request
`trace_id` (16-hex) and echoes it as the `X-Relay-Trace-Id` response
header — the same id appears on every log line of that request, so one
failing request filters out of the journal with
`journalctl --user -u iowap-server | grep "<trace_id>"`.

`/metrics`, `/ready`, and `/health` are intentionally open — the output
carries no secrets.

## How it works

Watch from outside (works from any host that can reach the relay):

```bash
curl -s http://relay-host:8788/health
# -> {"status":"ok","version":"...","mode":"core","event_subscribers":8}

curl -s http://relay-host:8788/ready
# -> {"status":"ready","database":true,...}

curl -s http://relay-host:8788/metrics | grep relay_nodes
# -> relay_nodes_total 4
# -> relay_nodes_online 3
# -> relay_queue_depth 0
```

The readiness status turns `degraded` when the maintenance loop stalls or
the last sweep errored — treat `ready` as the primary liveness signal,
`health` as the process check.

## What it is NOT

- **Not a distributed tracing system** — there are spans per request but
  no trace propagation across nodes; the `trace_id` binds relay logs and
  the response header, that is deliberately all (tracing was reviewed and
  rejected — it would break the relay's ahnungslos principle).
- **Not an alerting stack** — counters and gauges expose state; alerting
  is the scraper's job.

## Related pages

- [server setup](../server/setup.md) — logs, journal, systemd
- [tasks](tasks.md) — statuses observable per task/stage
- [API reference](../reference/api.md) — endpoint table
- [glossary](glossary.md) — verbatim terminology