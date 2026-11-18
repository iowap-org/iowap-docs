# Capability Recipes

> This section answers: **how do I turn *my thing* into an IOWAP
> capability?** Each recipe is a small, complete walkthrough built on one
> integration pattern, verified against a capability that runs in a real
> deployment (not a toy example).

## The one skeleton behind every recipe

Every capability — regardless of what it wraps — follows the same four
steps:

1. **Write a handler** — a script (or Python entry point) that reads the
   stage payload on stdin and prints a JSON result on stdout. Normative
   contract: [handler contract](../node/handlers/contract.md).
2. **Declare it in a capability profile** — name, version, handler path,
   `input_schema`, `timeout`, `max_parallel` (see
   [capabilities](../concepts/capabilities.md)).
3. **Publish** — `iowap-cli capabilities validate && iowap-cli capabilities
   publish`. The node heartbeats it to the relay; callers can route to it.
4. **Probe** — submit one real task end-to-end and check the result.

What changes between recipes is only step 1 — the shape of the wrapper:

| Recipe | Pattern | The wrapper does | Reference deployment |
|---|---|---|---|
| [Wrap an HTTP service](wrap-http-service.md) | network call | maps the payload to an OpenAI-compatible `/audio` or REST call | `stt.ai` / `tts.ai` (whisper + tts-1) |
| [Wrap a local binary](wrap-local-binary.md) | subprocess + artifacts | runs a local model binary, uploads the output file as an artifact | `image.generate.mflux` (FLUX on Apple silicon) |
| [Agent-to-agent chat](agent-to-agent-chat.md) | inbox capability + bridge adapter |
| [A long-running orchestrator](long-running-orchestrator.md) | long_run lease + forward slot + fan-out |
| [Long-running inference](long-running-inference.md) | long_run lease + progress notes | minutes-long model run with a live progress stream | video.gen.native (M4) + storage.archive | runs a whole pipeline, planner injected by the operator | `flow.run` (flow-runner) | writes inbound agent messages to a file inbox; replies are tasks | `a2a.inbox` across three agents |

The full deployment behind this catalog spans further patterns — long-running
workflows (`paperless.watch` → `flow.run`), device control (the `ha.*`
matrix from the HAOS app), large-file streaming (`storage.upload_channel` /
`download_channel` bridge routes), and container-fleet ops (the `mc.*`
family). Those get their own recipes over time; the skeleton above already
covers them.

## Choosing a pattern

| Your thing is… | Start with |
|---|---|
| A service that speaks HTTP (local or remote) | [wrap-http-service.md](wrap-http-service.md) |
| A binary or script on one specific machine | [wrap-local-binary.md](wrap-local-binary.md) |
| Something another agent should be able to talk to | [agent-to-agent-chat.md](agent-to-agent-chat.md) |
| Anything returning files (images, audio, documents) | wrap-local-binary.md — the artifact pattern applies |
| A multi-step pipeline | a handler that submits follow-up tasks (see `paperless.watch`, concepts: [flow](../concepts/flow.md)) |

## Rules that apply to every recipe

- **The relay never interprets your payload.** It routes the capability
  string; everything inside `{...}` is yours.
- **Fail loudly, finish cleanly.** Print the result envelope
  (`{"status": ..., "result": ...}`) or a non-zero exit with the error on
  stderr — the daemon turns that into task state.
- **Never touch the token.** The CLI primitives (`hp put/get`,
  `complete`, `note`) load credentials for you — see
  [handler primitives](../node/handlers/primitives.md).
- **Files ride the ladder, not the payload.** Inline base64 ≤ 5 MB,
  artifacts ≤ 50 MB, larger via a storage bridge — `hp put` picks the rung
  (see [artifacts](../concepts/artifacts.md)).
