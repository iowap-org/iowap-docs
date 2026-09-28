# Handler Contract (Envelope I/O)

> Normative reference for the JSON envelope exchanged between the node
> daemon and a handler script on every capability invocation. Introduced by
> the 2026-09-28 Envelope-Contract decision (T-005); the rollout is
> **tolerant** — see [Rollout tolerance](#rollout-tolerance) for what the
> daemon accepts while the fleet migrates.

Two different mechanisms are both called "envelope" in this codebase:

| Term | Mechanism | Documented in |
|---|---|---|
| **Handler result envelope** (this page) | the standardized request/response wrapper around every handler invocation | here — applies to every handler |
| **Transfer envelope** (`__iowap_ref__`) | opt-in file-transfer format for `node-cli hp put` / `hp get` | [handler-primitives.md](handler-primitives.md) |

They are unrelated; the name collision is historical. This page is only
about the handler result envelope.

## Request Envelope (daemon → handler stdin)

The daemon feeds every handler exactly this JSON object on **stdin**:

```json
{
  "task_id": "task_abc123",
  "capability": "chat.ai",
  "input": { "...capability-specific named fields..." }
}
```

| Field | Type | Meaning |
|---|---|---|
| `task_id` | `string`, non-empty | ID of the task the claimed stage belongs to |
| `capability` | `string`, non-empty | Name of the capability being executed |
| `input` | `object`, always present (possibly `{}`) | The capability-specific payload fields — exactly the payload the task was submitted with |

Rules:

- **Named fields only.** Contents of `input` are defined per capability by
  its `input_schema` (see [capabilities.md](capabilities.md)). There are no
  positional or numbered slots — reference fields by name.
- **`stage_id` is deliberately absent.** It identifies the claim, not the
  work. Handlers that need it read the `RELAY_STAGE_ID` environment
  variable (see the environment table in
  [capabilities.md](capabilities.md#handler-contract)).
- **Rollout mirroring (temporary).** While the fleet migrates, the daemon
  also places every `input` field at the **top level** of the stdin object,
  so handlers that still read flat keys (`payload.get("prompt")`) keep
  working unmodified. New handlers should read from `payload["input"]`;
  the top-level mirrors will be removed once every handler is migrated.
  If a payload field name collides with a contract key, the contract keys
  (`task_id`, `capability`, `input`) always win.

## Response Envelope (handler stdout → daemon)

On success a handler writes this JSON object to **stdout** and exits `0`:

```json
{
  "status": "completed",
  "result": { "...capability-specific named result fields..." },
  "error": null
}
```

On failure:

```json
{
  "status": "error",
  "result": null,
  "error": "Hermes timed out after 280s"
}
```

Rules (all normative):

| Rule | Detail |
|---|---|
| `status` | Literal `"completed"` or `"error"` — nothing else is valid |
| `result` | `object`, required when `status == "completed"` (may be `{}`); must be `null` when `status == "error"` |
| `error` | `string`, required when `status == "error"`; must be `null` when `status == "completed"` |
| exit code | `0` when a valid envelope was written; non-zero remains the hard-failure signal for infrastructural death (crash before emitting anything) |
| contents | Fields inside `result` are capability-specific **named fields** — the contract does not define them; machine-readable discovery is via `result_path_hints` (below) |

Extra top-level keys (e.g. `debug`) are tolerated and passed through
unchanged.

### Failure paths: in-band `status: "error"` vs exit codes

Both exist and both fail the stage (counted against the capability's
`max_retries`, so the scheduler retries and eventually marks the stage
`failed`):

- **In-band (`status: "error"`)** — the handler ran to completion and can
  describe the failure in one string. Use this for *expected, describable*
  failures: an upstream API rejected the request, the input is invalid, a
  timeout was hit inside the handler.
- **Out-of-band (non-zero exit)** — infrastructural death: the process
  crashed, was killed, or could not emit JSON at all. The daemon records
  `handler exited with code N` and captures stderr for debugging.

Do not exit `0` with a bare `{"error": ...}` dict in new handlers. That is
the legacy convention — still accepted during the rollout (it passes
through unchanged and fails the stage, see the tolerance table) — but the
envelope form is the contract going forward: only a dict with a `status`
key opts into envelope semantics, and a bare error dict has none.

## Named fields and `result_path_hints`

`result_path_hints` (advertised per capability in the capabilities
snapshot) are dot-paths **relative to the inner `result` object** of the
Response Envelope. A `chat.ai` handler that completes with
`{"status": "completed", "result": {"answer": "..."}}` advertises
`["answer"]`.

History (T-004 correction): hints were originally written
aggregate-relative (`result.answer`), which only worked while handlers
emitted bare results. With the envelope contract in place, the inner
`result` object is the stable reference frame — both for flow templates
(`${ref.result.path}` after the aggregate unwrap) and for machine-readable
hint discovery.

## Rollout tolerance

`handler_runner.run_handler()` normalizes handler stdout — the single
conversion point on every node. During the migration the daemon accepts
everything in this table; nothing here requires fleet-lockstep:

| Handler stdout (exit `0`) | What the daemon does |
|---|---|
| Conforming envelope (`status` present and valid) | Passes through **verbatim** — already-conforming handlers are never rewritten |
| Bare result dict without an `error` key | Wrapped into `{"status": "completed", "result": <dict>, "error": null}` |
| Bare dict **with** an `error` key (legacy error convention) | Passes through unchanged → stage fails, retry budget applies |
| Bare dict with a `result` key but **no** `status` | Wrapped (no `status` means not an envelope — only `status` opts into envelope semantics) |
| JSON that is not an object (list / string / number / bool / null) | Normalize error: `handler stdout must be a JSON object (envelope or bare result), got <type>` |
| Envelope with an invalid `status` value | Normalize error: `handler envelope has invalid status <value> (expected 'completed' or 'error')` |
| Envelope `status: "completed"` without a `result` object | Normalize error: `handler envelope status 'completed' missing 'result' object` |
| Envelope `status: "error"` without a string `error` | Normalize error: `handler envelope status 'error' missing 'error' message` |
| Not valid JSON at all | (unchanged) `handler stdout is not valid JSON: ...` |
| Empty stdout on exit `0` | (unchanged) `handler produced no stdout output` |
| Non-zero exit / timeout | (unchanged) `handler exited with code N` / `handler timeout after Ns` |

All normalize errors produce the standard error-result shape
`{"error": "<message>"}`, so failure/retry accounting is identical no
matter which path failed. Normalization is **idempotent**: a conforming
envelope is detected by its `status` key and passed through verbatim —
double-wrapping is impossible by construction.

Two edge cases worth knowing:

- A bare result that legitimately *contains* a `result` key but no
  `status` (e.g. `{"result": {...}}`) is **not** treated as an envelope —
  it gets wrapped: `{"status": "completed", "result": {"result": {...}}}`.
  Handlers must declare `status` to opt into envelope semantics.
- A dict that carries `status: "completed"` but no `result` key (a
  pre-convention shape some handlers once used) is a **normalize error**,
  not a pass-through — it cannot be interpreted under the contract.

## Relation to flows and the server

- The relay server stays a **dumb pass-through**: it stores `stage.result`
  verbatim and never parses, validates, or wraps envelope content.
- iowap-flow unwraps a completed envelope **exactly once** when joining
  stage results into the flow aggregate, so `${ref.result.path}` templates
  navigate the aggregate and the `path` segments are the capability's
  result field names (the `result_path_hints`). Bare results from
  not-yet-migrated handlers pass through unchanged — flows work against
  both handler generations during the rollout. See
  [capability-concept.md](capability-concept.md) for worked examples.

## See also

- [capabilities.md](capabilities.md#handler-contract) — handler environment
  variables, outcome table, profile validation
- [handler-primitives.md](handler-primitives.md) — opt-in primitives:
  `hp put`/`hp get` transfer envelopes, env-defaults, complete-by-script
- [capability-concept.md](capability-concept.md) — capability matching
  model and example handlers