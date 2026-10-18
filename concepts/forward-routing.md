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

## Relating events and errors

A refused slot submit is visible on the event bus as `forward_refused`
(payload `node_id`, `slot`, `reason`). Submit-side error codes are
`forward_mapping_missing` (422), `forward_mapping_invalid` (422) and
`forward_node_unknown` (404); mapping-management errors are
`target_unknown_capability` (422) and `redirect_self` (400). The full table:
[API reference](../reference/api.md#forward-routing-relayv2forward-mappings).

## Limits

- One hop: a mapping target is a real capability, so cascade forwarding
  (forward → forward) cannot be configured today.
- `forward` is a submit-time concern: a task submitted directly against the
  real target capability already routes normally, and the relay never
  advertises `forward` as an available capability.