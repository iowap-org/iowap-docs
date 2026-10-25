# Forward Routing

Forward routing lets one node hand its stage to another capability without
knowing which node will execute it: the submitter targets the relay-side
pseudo-capability `forward` with a slot number, and the relay rewrites the
stage to the target capability configured for that submitter and slot.

The feature solves node-to-node capability dependencies. A node that knows
"my result feeds slot 1 into the next step" submits against `forward` and
never needs the target's name, provider or address wired into its code. The
mapping lives server-side; the operator controls it.

## Mapping model

A mapping is one `(node_id, slot) → target_capability` row in the
`forward_mappings` table:

- **Slots are per-node.** The same slot number on two nodes may map to two
  different targets — slot `"1"` means "node A's step 1", not a global
  channel.
- **Slot names** are strings of letters, digits, `_` and `-` (1–64 chars,
  trimmed): `"1"`, `"a"`, `"s-2"`.
- **Targets are real capabilities** from the capability catalog. Availability
  is not required to store a mapping — a task queues pending under the target
  until a provider is free, like any submitted task.
- `forward` itself is never a valid target (a trivial loop is refused with
  `400 redirect_self`).

Mappings are managed by an admin — via the
[API](../reference/api.md#forward-routing-relayv2forward-mappings) or the
node profile page in the dashboard. A node cannot register mappings itself,
and `forward` is never advertised in a node's capabilities.

## Submit flow

1. **Submit.** The node submits a stage with `capability: "forward"` and
   `payload.forward_slot`. `submitted_by` is the authenticated node
   (server-derived, as for every submit).
2. **Resolve.** The relay loads the mapping `(submitted_by, forward_slot)`.
   No mapping → `422 forward_mapping_missing`; malformed slot →
   `422 forward_mapping_invalid`; unknown submitter →
   `404 forward_node_unknown`. A refused submit creates no task.
3. **Rewrite.** On success the stage's capability becomes the target and the
   slot is stored on the stage as provenance (`forward_slot`) for stage
   detail and auditing. The task keeps its one ID — a redirect is a
   submit-time rewrite, not a re-submission. The claiming node receives the
   payload shaped for the real target, without the slot key.
4. **Claim.** The stage becomes a normal pending claim under the target
   capability: only nodes advertising exactly the resolved target can claim
   it. On claim the single-stage task's `owner_node_id` flips to the
   claiming node; `submitted_by` stays the original sender (see
   [tasks](tasks.md) for the visibility model).

Worked cURL examples: [the API reference](../reference/api.md#forward-routing).

## Typed slots

Since migration 16 a declared slot carries a **type**. The declaration is
node-owned metadata: a node heartbeats its `forward_slots` entries (see
[node config](../node/config.md#forward-slots)) and the relay validates and
stores them. The registry is exactly `forward`, `text` and `bool`; an
absent `type` resolves to `forward`, so pre-typed-slot declarations keep
working unchanged.

- **`forward`** — the classic routing handle: no `value` (the target lives
  in `forward_mappings`), no refs; `input_schema` is allowed as a
  structure-only dict (its contents stay unvalidated until the T-247
  payload contract exists).
- **`text` / `bool`** — value slots. A `text` value must be a string, a
  `bool` value a real boolean (`"true"` / `1` are refused — no coercion).
  Value slots may declare a **ref** as a whole pair (`ref_slot` +
  `ref_field`); the referenced slot must be a `forward` slot of the same
  declaration (value slots are never referable, so refs cannot cycle).
- Types are matched exactly (trimmed, case-sensitive): unknown, empty or
  mis-typed values are a loud `422 forward_slot_invalid`. A rejected
  declaration never touches existing rows — validation runs before the
  store is replaced, and the heartbeat stays `200` (swallow-and-log).

### Submit gate

A submit against a slot explicitly declared `text` or `bool` is refused
with `422 forward_slot_not_routable` **before** mapping resolution — a
value slot has no routing target by definition, so the error names the
declared type as the real cause. Undeclared slots and legacy rows without
a stored type keep routing unchanged. The refusal carries no
`forward_refused` event: gate refusals are configuration errors (the
declaration needs a fix on the node), not runtime refusals.

## Provider pin

Since migration 17 a mapping can optionally be **pinned** to one concrete
node: `forward_mappings.target_node_id`. `NULL` = no pin = the legacy "any
capable provider" behaviour (no backfill — every pre-existing mapping is
unpinned by definition). The pin answers the schema-drift problem: when the
same capability is advertised by nodes with different `input_schema` shapes,
pinning makes the executing node — and therefore the payload contract —
exact instead of "whatever provider claims first". The dashboard shows the
pin as the node's name in the mapping table ("Provider" column) and marks
unpinned mappings with a visible **"Provider variabel"** badge — the drift
location to fix.

- **The pin is the execution address, orthogonal to visibility.** It lives
  on the **stage** (`task_stages.target_node_id`, copied from the mapping at
  submit time), not on `tasks.owner_node_id`: the task owner is the T-227
  visibility semantics and stays untouched (the claimer of a single-stage
  task still flips the owner; multi-stage fan-out tasks never flip, and
  each forward stage of one task may carry a different pin).
- **Hard validation at PUT** (the admin's config, validated when it is
  written): the pin node must exist (`422 target_node_unknown`) and it must
  advertise the mapping's target capability **itself** — a node-scoped row
  read, never the catalog aggregate (`422
  target_node_lacks_capability`). The pin form is a plain string (trimmed,
  64-char cap; `422 target_node_invalid` otherwise, e.g. over length);
  mis-typed values are rejected by the body model (a pydantic list-422).
  Unpinned PUTs keep the legacy ladder byte-identical, including its
  aggregate catalog check.
- **Submit and claim:** the submit-time rewrite copies the pin onto the
  stage next to the resolved capability; the claim gate then accepts a
  pinned stage only from its pin target (`s.target_node_id IS NULL OR
  s.target_node_id = <claimer>`). Undeclared pins keep the first-claimer-
  wins semantics. A **pending stage whose pin target no longer exists** is
  failed at claim time instead of pending forever (the pre-SELECT dead-pin
  sweep — the owner-deleted analogue), eventless like every stage-level
  fail.
- **Unpin rule:** the PUT is a full-row replace — a body that **omits**
  `target_node_id` (or sends `""`) unpins the mapping on every save, exactly
  like `target_capability` replacement. Deleting the pinned **node** keeps
  the routing definition and voids the pin: mappings pinned at the deleted
  node and their stages read `NULL` ("provider variabel") after the delete,
  and the submitters' mapping rows survive.
- A pinned stage that is also owned by another node (owner ≠ pin, both
  alive) is permanently pending — the two gates are orthogonal by design.
  Pin and slot timeout belong together: a fallen provider blocks the task
  deterministically until the timeout instead of self-healing to another
  provider.

## Relating events and errors

A refused slot submit is visible on the event bus as `forward_refused`
(payload `node_id`, `slot`, `reason`). Submit-side error codes are
`forward_mapping_missing` (422), `forward_mapping_invalid` (422) and
`forward_node_unknown` (404); typed-slot codes add
`forward_slot_not_routable` (422, submit against a declared value slot —
no `forward_refused` event) and the declaration-side `forward_slot_invalid`
(422, heartbeat-scoped). Mapping-management errors are
`target_unknown_capability` (422), `redirect_self` (400) and the pin codes
`target_node_invalid` / `target_node_unknown` /
`target_node_lacks_capability` (422, PUT-scoped, see
[provider pin](#provider-pin)). The full table:
[API reference](../reference/api.md#forward-routing-relayv2forward-mappings).

## Limits

- One hop: a mapping target is a real capability, so cascade forwarding
  (forward → forward) cannot be configured today.
- `forward` is a submit-time concern: a task submitted directly against the
  real target capability already routes normally, and the relay never
  advertises `forward` as an available capability.
