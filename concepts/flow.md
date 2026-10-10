# Flow

This page answers: what is a flow, how does planning/fan-out/aggregation
work, and what does the runner do — without getting intelligence?

## What it is

A **flow** is a compound task: one origin request planned into an execution
DAG, fanned out as ordinary relay tasks, joined, and aggregated back.
The executor is the **flow runner** — an orchestrator node advertising the
`flow.run` capability (separate repo/image:
[iowap-org/iowap-flow](https://github.com/iowap-org/iowap-flow)). The relay
stays dumb: a flow is just a claimed stage that runs long; every step
crosses the relay's normal scheduler.

It is a deliberate **dumb Kanban**: the runner holds no intelligence of its
own. Planning is delegated to an `agent.ai` planning task; then the runner
is strictly mechanical — validate, fan out, poll, aggregate, fail-fast.

```
origin task (flow.run)                      ── long_run lease + keepalive notes
   │ 1. note "flow started"
   │ 2. discovery snapshot (capabilities + result_path_hints)
   │ 3. planning task → agent.ai ("plan this request; here's the valid capability set")
   │ 4. plan = small DAG {task_ref, capability, payload, depends_on}
   │ 5. validate plan against a FRESH snapshot (plan↔execution race guard)
   │ 6. fan out: submit every dependency-free task simultaneously
   │    (idempotency_key flow-<origin>-<ref>, ordinary relay tasks)
   │ 7. poll loop (5 s) + keepalive note every 600 s ("done=K/N")
   │ 8. every failed child (permanent) → whole flow fails, clear reason
   │ 9. join: aggregate {task_ref: result} → complete origin stage
   ▼
origin result: {status: completed, aggregate, summary}
```

## How it works

### Planning

The runner builds a planner prompt (frozen template): the original request
plus the capability snapshot — capabilities live (`available: true`),
with **`result_path_hints`** for template planning. The planner returns a
JSON plan (code fences tolerated); parsing failing twice fails the flow.
The plan is only executed after revalidation against a fresh discovery
snapshot — a capability that vanished between planning and execution fails
the flow instead of silently skipping.

### Fan-out and dependencies

Tasks submit topologically: every task whose `depends_on` is complete goes
out at once (true parallelism across nodes). Each child is an ordinary
relay task — claim, capability match, retries all work unchanged. The
runner injects `flow: {origin_task_id, task_ref}` metadata into children
when the capability's `input_schema` allows an extra field.

### Data injection (`${ref.result.path}`)

Payloads can reference earlier task results via templates resolved at
submit time from the running aggregate:

```json
{"summary": "${report.result.answer}", "image": "${img.result.artifact_id}"}
```

`ref` must be listed in the child's `depends_on` — unresolved references
fail fast with the available result keys in the error. Path segments are
**relative to the handler result envelope's inner `result` object** (so
`report.result.answer` resolves to the chat answer itself); a capability
without `result_path_hints` can still be referenced once an earlier run
shaped the aggregate — hints exist so the planner doesn't have to guess.

### Catalog, history, and modes

Completed plans are recorded to local history (retention-cleaned); a plan
can be promoted to the named **catalog** (`save_flow`) and re-run
parameterized (`run_flow` + `${input.path}` from the caller's payload).
`list_flows` reports the catalog. Modes arrive in the flow payload
(`mode: list_flows | run_flow | save_flow`); without `mode` the runner
plans fresh.

### Failure semantics

- A permanently failed child fails the whole flow immediately, with a
  note naming the task ref and reason. No partial retry of the flow.
- Relay outages during polling degrade to exponential backoff (up to
  60 s), then abort the flow — no silent hangs.
- The origin stage holds a **long-run lease** (2 h TTL, refreshed by
  keepalive notes every 600 s) for the entire flow duration — the
  `flow.run` capability is profiled `long_run: true`, so no claim-TTL race
  kills a multi-node flow.

## What it is NOT

- **Not a server feature** — the relay never parses plans or aggregates;
  all orchestration lives on the runner node (the relay stays ahnungslos
  by construction).
- **Not a workflow engine with conditionals** — the plan is a DAG of
  submit-order edges; branching inside tasks is the task's business.
- **Not durable** — history/catalog live in the runner container's volume;
  the relay sees only the origin task's result.

## Related pages

- [nodes](nodes.md) — the orchestrator is an ordinary node
- [tasks](tasks.md) — what children are from the relay's view
- [capabilities](capabilities.md) — `result_path_hints` semantics
- [flow runner deployment](../flow/runner.md) — the shipping runner