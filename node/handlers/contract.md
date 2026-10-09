# Handler Contract

> Normative reference — the JSON envelope exchanged between the node
> daemon and a handler script on every capability invocation. Applies to
> every handler; the rollout is tolerant while the fleet migrates.

Two things are called "envelope" in this codebase — they are unrelated
(the collision is historical):

| Term | Mechanism | Reference |
|------|-----------|-----------|
| **Handler result envelope** (this page) | Standard request/response wrapper around every handler invocation | here |
| **Transfer envelope** (`__iowap_ref__`) | Opt-in file transfer for `node-cli hp put/get` | [handler primitives](primitives.md) |

## Request envelope (daemon → handler stdin)

Exactly this JSON object arrives on **stdin**:

```json
{
  "task_id": "task_abc123",
  "capability": "chat.ai",
  "input": { "prompt": "…capability-specific named fields…" }
}
```

| Field | Type | Meaning |
|---|---|---|
| `task_id` | string, non-empty | ID of the task the claimed stage belongs to |
| `capability` | string, non-empty | Name of the capability being executed |
| `input` | object (possibly `{}`) | The capability-specific payload — named fields, defined by the capability's `input_schema`; no positional/numbered slots |

Rules:

- **`stage_id` is deliberately absent** — it identifies the claim, not the
  work. Handlers needing it read the `RELAY_STAGE_ID` environment
  variable.
- **Rollout mirroring (temporary):** while the fleet migrates, the daemon
  also places every `input` field at the **top level** of the stdin object
  (old flat handlers keep working). New handlers read `payload["input"]`;
  the mirrors will be removed once every handler is migrated. On name
  collisions the contract keys (`task_id`, `capability`, `input`) win.

## Response envelope (handler stdout → daemon)

Success — write this JSON to **stdout**, exit `0`:

```json
{ "status": "completed", "result": { "answer": "…" }, "error": null }
```

Failure (in-band):

```json
{ "status": "error", "result": null, "error": "upstream API rejected the request" }
```

| Rule | Detail |
|---|---|
| `status` | Literal `"completed"` or `"error"` — nothing else is valid |
| `result` | object, required when `status == "completed"` (may be `{}`); absent/null otherwise |
| `error` | string, required when `status == "error"` |
| exit code | `0` when a valid envelope was written; non-zero = infrastructural death (crash, no JSON possible) |
| contents | Fields inside `result` are capability-specific **named fields** — machine-readable discovery via `result_path_hints` (below) |

Extra top-level keys (e.g. `debug`) are tolerated and passed through.

### Two failure paths

Both fail the stage and burn the capability's retry budget:

- **In-band (`status: "error"`)** — the handler ran to completion and can
  describe the failure in a string (upstream rejected, invalid input,
  internal timeout). This is the normal error path.
- **Out-of-band (non-zero exit)** — infrastructural death: crash, kill,
  no JSON possible. The daemon records `handler exited with code N` and
  captures stderr for debugging.

Legacy convention (exit `0` with a bare `{"error": …}` dict) — do not use
it in new handlers; see the tolerance table.

## Normalization and rollout tolerance

`handler_runner.run_handler()` is the single conversion point on every
node — normalizing is idempotent (a conforming envelope is detected by
its `status` key and passed through **verbatim**, so double-wrapping is
impossible):

| Handler stdout (exit 0) | What the daemon does |
|---|---|
| Conforming envelope (`status` present and valid) | Passes through **verbatim** |
| Bare result dict without an `error` key | Wrapped into `{"status": "completed", "result": …, "error": null}` |
| Bare dict **with** an `error` key (legacy) | Passes through unchanged → stage fails, retry budget applies |
| Bare dict with a `result` key but **no** `status` | Wrapped (only `status` opts into envelope semantics) |
| Non-object JSON (list/string/number/bool/null) | Error: `handler stdout must be a JSON object (envelope or bare result), got <type>` |
| Envelope with an invalid `status` value | Error: `handler envelope has invalid status <value> (expected 'completed' or 'error')` |
| `status: "completed"` without a `result` object | Error: `handler envelope status 'completed' missing 'result' object` |
| `status: "error"` without a string `error` | Error: `handler envelope status 'error' missing 'error' message` |
| Not valid JSON at all | Error: `handler stdout is not valid JSON: …` |
| Empty stdout on exit 0 | Error: `handler produced no stdout output` |
| Non-zero exit / timeout | Error: `handler exited with code N` / `handler timeout after Ns` |

All normalize errors produce the standard error result shape
`{"error": "<message>"}` — failure/retry accounting is identical no matter
which path failed.

## `result_path_hints`

Hints (advertised per capability) are dot-paths **relative to the inner
`result` object** of the Response Envelope: a handler completing
`{"status": "completed", "result": {"answer": "…"}}` advertises
`["answer"]`. Consumers (flow templates `${ref.result.path}`) navigate the
aggregate after unwrapping exactly one envelope layer.

## Who parses what

- **The relay server stays a pure pass-through** — it stores
  `stage.result` verbatim, never parses or wraps envelope content.
- **iowap-flow unwraps exactly once** when joining stage results into the
  flow aggregate (it is a consumer; the relay is not).
- **CLI consumers of `stages[].result` unwrap one envelope layer** —
  conforming handlers pass through verbatim, so the CLI sees the Response
  Envelope itself, not the inner result (helper:
  `nodes.common.cli.cli_bridge._find_result`; legacy flat results pass
  through unchanged; an envelope with `status: "error"` or a set `error`
  yields nothing — failed work).

## Related pages

- [handler primitives](primitives.md) — opt-in file transfer, complete-by-script
- [capabilities how-to](../capabilities.md) — env vars, profile validation
- [tasks](../../concepts/tasks.md) — retry/failure accounting