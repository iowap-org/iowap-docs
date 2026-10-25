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
  in `forward_mappings`), no refs; `input_schema` is an object whose
  structure is validated at declaration (dict-or-422). Since T-247 the
  declared field names carry weight beyond structure: they are the
  `ref_field` universe of the declaration (schema-gated refs, see below)
  and the validation universe for un-pinned binding targets.
- **`text` / `bool`** — value slots. A `text` value must be a string, a
  `bool` value a real boolean (`"true"` / `1` are refused — no coercion).
  Value slots may declare a **ref** as a whole pair (`ref_slot` +
  `ref_field`); the referenced slot must be a `forward` slot of the same
  declaration (value slots are never referable, so refs cannot cycle).
  Since T-247 the ref is also **content-checked**: the referenced slot
  must declare an `input_schema` and its `ref_field` must be one of the
  declared field names — a schema-less or unknown-field ref is refused
  (this fulfills the T-245 deferral, D-09).
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

## Payload binding

Since migration 18 a mapping may carry an optional **payload binding**:
`forward_mappings.binding` is a JSON text of the form
`{"rules": [{"sources": ["…"], "target": "…"}], "separator": "…"}`.
`NULL` / omitted = **legacy 1:1 passthrough** (no backfill — the mapping
keeps its behaviour). One rule with **one** `sources` entry copies that
payload field's value into `target`; **several** entries join the present
values with `separator` (default `"\n\n"`, any content allowed including
the empty string — adjacent join). Rule `target`s are **disjoint**
across rules (a duplicate would make the projection order-dependent and
is refused at PUT). Rules fire in order: a rule with none of its source
fields present stays dormant (writes and consumes nothing), a fired rule
**consumes** its matched sources, and a later rule may read an earlier
rule's target (chaining is deterministic).

- **Unbound fields fly.** After the last rule every payload key that is
  neither a written target nor a **reserved prompt field** is dropped —
  deliberate anti-drift (a rewrite should not carry arbitrary junk into
  the provider's payload). The reserved set is
  `task`, `prompt`, `question`, `message`, `input`, `systemprompt`,
  `taskprompt` — the verbatim mirror
  of the flow handler's prompt channel (`PROMPT_KEYS` chain plus the
  plan-split fields), so a handler's prompt
  channel cannot be eaten by an unbinding rewrite. On the plan-split
  channel the flow planner submits `systemprompt`/`taskprompt` as a pair;
  they survive the sweep unless a rule consumes them, so both the unbound
  handler join and a future binding reproduce the full prompt. A reserved
  field that
  a rule actually binds (as source or target) does **not** double-survive
  — "survives unless consumed".
- **Hard validation at the PUT** (the mapping is admin config; a config
  error must be loud at write time, not at some later submit):
  - the **form** is validated first — wrong shapes, padded/empty/oversized
    names, non-list `sources`, an optional `separator` that is not a
    string → `422 forward_binding_invalid`;
  - **sources** are validated against the submitter's declared slot
    `input_schema` when the slot declares one (`422
    forward_binding_unknown_source_field`); a slot without a schema keeps
    free payload field names (the payload itself is the universe at
    submit, a dead source is simply dormant);
  - **targets** are hard in both branches: a **pinned** mapping validates
    against the pin node's own `input_schema` row for the target
    capability (node-scoped, never the aggregate — `422
    forward_binding_unknown_target_field` when the schema names the
    field nowhere, `422 forward_binding_requires_schema` when the
    provider declares no schema at all); an **un-pinned** mapping
    validates against the same slot schema as the sources (absent schema
    → `forward_binding_requires_schema` — un-pinned bindings require the
    submitter to declare its contract).
- **Submit-time rewrite.** The binding projects the stage payload during
  the existing forward rewrite (one task ID, no re-submit, no third
  mode): payload-only — claim gates, owner semantics and the
  `forward_refused` event gate stay untouched. The stored stage payload
  remains a JSON string (the rewrite result is serialized as-is). A
  **corrupt stored binding** (invalid JSON or a shape that no longer
  passes the form validation) refuses the submit loudly with `422
  forward_binding_invalid` — never a silent passthrough — and carries no
  event (configuration error, not a slot refusal). Mappings **without a
  binding behave byte-identically** to the pre-binding behaviour.
- **Full-row replace / no auto-unbind.** Like the pin, the binding is
  replaced on every PUT: omitting `binding` unbinds (legacy passthrough).
  The binding stores field *names* — no reference to any row — so when a
  provider's schema loses a field later (heartbeat re-declare), the
  binding keeps its deterministic projection and the row **displays**
  its state in the dashboard ("Binding" column); the next PUT
  re-validates against the then-current schema and fails loudly there.
  The admin surface is the correction path (no silent auto-unbind).

This fulfills the two T-245 deferrals: **D-05** (the slot/input_schema
field contract) is the binding PUT validation above plus the
schema-gated refs described in [typed slots](#typed-slots); **D-09**
(the `ref_field` content check) is the declaration-side ref validation.

The dashboard's mapping editor renders rule rows with **source chips**
(from the submitter's declared slot schema; free-name inputs when the
slot declares no schema), a **target field** with suggestions from the
target capability's schema, a **separator** input, and a **"match by
name"** helper that prefills 1:1 rules from the schema intersection.
Clearing every rule and saving sends `binding: null` (legacy).

## Relating events and errors

A refused slot submit is visible on the event bus as `forward_refused`
(payload `node_id`, `slot`, `reason`). Submit-side error codes are
`forward_mapping_missing` (422), `forward_mapping_invalid` (422) and
`forward_node_unknown` (404); typed-slot codes add
`forward_slot_not_routable` (422, submit against a declared value slot —
no `forward_refused` event) and the declaration-side `forward_slot_invalid`
(422, heartbeat-scoped, including the schema-gated ref checks).
Mapping-management errors are
`target_unknown_capability` (422), `redirect_self` (400), the pin codes
`target_node_invalid` / `target_node_unknown` /
`target_node_lacks_capability` (422, PUT-scoped, see
[provider pin](#provider-pin)) and the binding codes
`forward_binding_invalid` / `forward_binding_unknown_source_field` /
`forward_binding_unknown_target_field` /
`forward_binding_requires_schema` (422, PUT-scoped and — for corrupt
stored binding state — submit-scoped, see [payload
binding](#payload-binding)). The full table:
[API reference](../reference/api.md#forward-routing-relayv2forward-mappings).

## Limits

- One hop: a mapping target is a real capability, so cascade forwarding
  (forward → forward) cannot be configured today.
- `forward` is a submit-time concern: a task submitted directly against the
  real target capability already routes normally, and the relay never
  advertises `forward` as an available capability.
