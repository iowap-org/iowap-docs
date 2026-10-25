# Flow Runner

Deployment and operation of the shipping flow runner — the node that
executes `flow.run`. The model: [concept: flow](../concepts/flow.md).

## What it is

The runner is an ordinary node built on the iowap-node framework
(pinned dependency) carrying exactly one workflow capability:

```yaml
# profiles/node.yaml (repo, baked into the image)
node_name: flow-runner
capabilities:
  - name: flow.run
    type: workflow
    claimable: true
    long_run: true        # lease instead of the 300 s claim timeout
    max_parallel: 1       # one Kanban per node
    timeout: 14400        # 4 h handler budget
    input_schema:
      fields:
        original_request: { name: original_request, type: string, required: true }
        options: { name: options, type: object, required: false }
    handler: python3 /app/handlers/flow_run.py
```

Sub-repo: [iowap-org/iowap-flow](https://github.com/iowap-org/iowap-flow)
(handlers, runner pipeline in `src/flow_node/`, 17 test files). Image:
`ghcr.io/iowap-org/iowap-flow` (built from the repo's `Dockerfile`;
base image `iowap-node-base`).

## Running it

```bash
docker run -d \
  --name flow-runner \
  --restart unless-stopped \
  -e RELAY_URL=http://192.0.2.60:8788 \
  -e NODE_NAME=flow-runner \
  -v flow-state:/home/appuser/.relay \
  ghcr.io/iowap-org/iowap-flow:latest
```

The **state volume is the node identity** (node_id, tokens, catalog,
history) — without it the container re-registers and needs re-approval
on every restart. Approval via the relay dashboard once, then it stays.

The entrypoint handles relay discovery fallback (mDNS) when `RELAY_URL`
is unset — pin the URL for fixed installations.

## Submitting a flow

```bash
node-cli task submit \
  --stage "flow.run:{\"task\": \"Create 3 product images and zip them\"}" | jq
# -> {"task_id": "tsk_...", "status": "pending"}
node-cli task wait <task_id> --interval 15 | jq
# -> {status:"completed", ...}
```

The result carries `{flow: ..., aggregate: {task_ref: result, …},
summary: …}`. Watch progress live: keepalive notes on the origin task
(`node-cli task result <task_id>`) and every child as an ordinary task in
the scheduler view.

Re-run a catalog flow:

```bash
node-cli task submit \
  --stage 'flow.run:{"mode": "run_flow", "flow": "weekly-report",
           "input": {"path": "/data/report.html"}}' | jq
```

### Plan prompt split (`FLOW_PLAN_PROMPT_SPLIT`)

With the env `FLOW_PLAN_PROMPT_SPLIT=1` in the runner container the
plan-phase submit sends the prompt as **two payload fields** instead of
one `task` string:

- `systemprompt` — the frozen planner contract (output format, plan
  schema, data-sharing rules); static,
- `taskprompt` — the task plus the capabilities snapshot; on a retry the
  validation feedback is appended here,
- `forward_slot` — unchanged (`plan`).

Default **off**: without the env the runner submits the legacy single
`task` payload (byte-identical behavior; rollback = recreate the container
without the env). At binding-NULL mappings the payload passes the relay
through 1:1 and the `agent.ai` handler merges the pair — `systemprompt`,
one blank line, `taskprompt`; a later binding reproduces the same join
via the binding default separator.

## Operational notes

- **One Kanban per node** (`max_parallel: 1`): parallelise flows by
  starting a second runner container, not by raising this.
- **Poll cadence** 5 s per child; relay outages back off to 60 s; after
  ~9 consecutive errors the flow aborts (no silent hangs).
- **History retention** cleans old runs automatically (volume-bounded);
  promote keepers to the catalog via `mode: save_flow` + `history_id`.
- **Envelope migration** — the stdin strip accepts all three
  handler-runner generations (pre-envelope flat, mirrored, strict), so
  runners on older iowap-node wheels keep working while the fleet rolls.
- Keepalive notes refresh the origin lease every 600 s — deleting the
  origin task mid-flow also kills the runner's completion path.

## Verification

```bash
node-cli node info flow-runner   # capability + status live
node-cli task result <origin_id> # aggregate + summary after completion
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Flow fails "plan attempt 1+2 invalid" | planner couldn't produce valid JSON with the given capabilities — check `agent.ai` provider is live and the plan prompt's snapshot contains the needed caps |
| `template … unresolved: task … not in aggregate` | the referenced task is missing from `depends_on` — add it |
| Flow fails at a child | read the origin note ("flow failed at ×: reason") — the child's error is final after retries |
| Runner never completes, notes stop | origin task deleted or lease dead — resubmit |
| Container re-registers after restart | missing state volume (see above) |
| Stale planner output (fenced JSON) | tolerated (fences stripped); a planner still failing twice fails the flow by design |

## Related pages

- [concept: flow](../concepts/flow.md) — the model behind the runner
- [node setup](../node/setup.md) — generic node installation
- [capabilities how-to](../node/capabilities.md) — profiles and `long_run`
- [tasks](../concepts/tasks.md) — leases and keepalive notes