# Recipe: A Long-Running Orchestrator Node (flow runner)

> End state: one node that orchestrates a whole pipeline — holds a lease
> for as long as it runs, fans work out as plain tasks, and gets its one
> external dependency (the planner) injected by the operator through a
> forward slot instead of hardcoded into the handler. Reference
> deployment: the `flow-runner` node (`flow.run` + `flow.catalog`),
> production on a NAS container.

## What you'll end up with

```text
caller ── task submit flow.run:{original_request} ──▶ relay ──▶ flow-runner (long_run lease)
                                                               │ handler: plan → fan-out → join
        ── forward slot "plan" ──────────────────────────────▶ relay rewrites to the mapped
        (in-place, one task id)                                 planner capability (operator choice)
        ── child tasks (doc.process, image.gen, …) ──────────▶ other nodes, plain task routing
caller ◀── result: flow verdict ───────────────────────────────┘
```

Three capabilities problems in one deployment — this recipe covers all
three:

1. **Long-running stage**: the handler runs minutes-to-hours and must
   survive the 300 s claim TTL.
2. **Dependency injection**: the handler needs an LLM planner but must not
   hardcode *which* one — the operator decides per deployment.
3. **Fan-out orchestration**: child steps are ordinary tasks to other
   nodes; the orchestrator collects and joins.

## Ingredients

- A node with iowap-node ≥ 2.3.44 (flow-runner runs in a container on the
  NAS; any host works)
- An agent-capable node somewhere in the fabric to plan with (any
  capability you later map into the slot)
- A profile with three declarations: the workflow capability, its
  `long_run: true` flag, and the forward slot

## Steps

### 1. Declare the workflow capability with `long_run: true`

```yaml
capabilities:
- name: flow.run
  version: "1.0.0"
  claimable: true
  long_run: true          # THE flag: lease instead of the 300 s claim timeout
  type: workflow
  max_parallel: 1         # one flow per node — serial plan execution
  handler: /app/handlers/flow_runner.py
  timeout: 7200           # ceiling for a full flow; the lease outlives it
  description: 'Accepts a planned flow request and executes it as plain
    tasks. Input: original_request, optional mode=run_flow.'
```

That one flag changes the stage mechanics: instead of the default claim
TTL, the handler **holds a lease and keeps it alive with keepalive task
notes** (`iowap-cli task note "step 2/5 …"`); the accepted-stage TTL
extends to 2 h (T-154). Without it, a 10-minute handler risks the
T-213 race — the stage finishes after TTL loss and the result is
discarded. Normative background: [tasks](../concepts/tasks.md),
[handler primitives](../node/handlers/primitives.md#note).

### 2. Declare the forward slot (the dependency)

The handler needs a planner, but *which* planner is the operator's call.
So the profile declares a **slot** — a named dependency with an input
schema, not a target:

```yaml
forward_slots:
  "plan":
    label: "Planner"
    description: "Planner dependency for flow planning (LLM/decision model)."
    input_schema:
      fields:
        instruction:  {name: instruction, type: string,  required: false}
        task:         {name: task,        type: string,  required: false}
        capabilities: {name: capabilities, type: array,  required: false}
        schema:       {name: schema,      type: object,  required: false}
```

Notes baked into the real deployment:

- **Fields as declared payload channels.** The runner ships
  `instruction`, `task` and the live `capabilities` list as schema fields
  — the planner is NOT an agent, it receives everything it needs in the
  payload (T-254).
- **Const binding rules ride server-side.** The workflow schema for
  structured outputs is enforced as a server-side const rule on the slot
  (T-252), so the planner's output is validated before the runner sees it.
- **Value slots as admin defaults.** Optional `value:` entries (e.g.
  `think: false`) are injected into every forward submit where the runner
  does not send the field itself — payload wins (T-253).

### 3. The operator maps the slot — server-side, per node

The handler submits against the pseudo-capability `forward` with
`forward_slot: "plan"`. The relay **rewrites the stage in place** (same
task id, no re-submit) to whatever the `forward_mappings` row says:

```text
(node_id, slot) → target capability
```

Slots are **per-node**: another node's `"plan"` can map to a different
planner. Swapping the LLM behind the flow runner is a one-row dashboard
change — the handler code never mentions a capability name. Model:
[forward-routing](../concepts/forward-routing.md). Live example in this
deployment: slot `"plan"` on the flow node → `agent.ai` (and five
numbered slots on the desktop node for decision/classification/archive
steps).

### 4. The handler — plan, fan out, join, keepalive

The handler's loop in prose (real code: flow-runner repo):

1. Read the request; submit `forward` with `forward_slot: "plan"` plus
   instruction/task/capabilities — get a *plan* (list of
   `{capability, payload, why}`) back in the stage result.
2. **Fan out**: every plan step becomes a child task via ordinary
   `task submit` — plain routing to whatever node owns the capability.
3. **Keepalive**: between polls, append a task note — this is what holds
   the lease alive.
4. **Join + finish**: collect child results, aggregate, print the result
   envelope. The long stage completes cleanly even after an hour.

### 5. Probe

```console
$ iowap-cli capabilities validate && iowap-cli capabilities publish
$ iowap-cli task submit --name flow-smoke \
    --stage 'flow.run:{"original_request":"convert the newest paperless doc to a summary task"}' \
    --owner <your-node-id>
$ iowap-cli task wait <task_id>          # note the keepalive notes while it runs
```

## Variations

- **Watcher starter** (`paperless.watch`): the same `long_run: true` flag,
  but the loop is a *consume-poll* — detect, fetch, upload an artifact,
  submit a downstream flow — then exit. Long-run is per-invocation, not
  per-week: the daemon stays idle between polls.
- **CPU batches** (`storage.archive`/`storage.extract`): long_run +
  progress notes (T-160) on a plain packing job — the simplest possible
  lease consumer.
- **Named slots instead of numbered:** slot names are `[A-Za-z0-9_-]{1,64}`
  — a node with several dependencies uses readable names (`"plan"`,
  `"classifier"`, `"archive"`), the numbering in this deployment's other
  node is history.
- **No planner needed?** Drop the slot, keep steps 1/3/4 — the recipe
  degrades gracefully to a plain long-running fan-out node.

## Why this recipe earns its length

It composes **three** fabric concepts in one deployment — lease semantics
(`long_run`), operator-owned dependency routing (`forward` slots), and
plain task fan-out — without a single line of orchestration code in the
relay. The orchestrator is a handler on a node; the fabric stays a router.
