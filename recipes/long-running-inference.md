# Recipe: Long-Running Inference (the Lease)

> End state: a capability whose work takes *minutes*, survives the default
> claim timeout, streams visible progress to the caller, and returns a
> file. Reference deployment: `video.gen.native` (MiniMax H3 on the M4 Mac,
> native Metal) — the deliberate **upgrade path** of
> [wrap a local binary](wrap-local-binary.md): same shape, plus the
> `long_run` lease and a progress loop. The CPU-batch sibling of this
> pattern is `storage.archive` (tar.gz packing, progress notes, ~4 lines
> of extra handler).

## What you'll end up with

```text
caller ── task submit video.gen.native:{prompt} ──▶ relay ──▶ the model node
     ◀── task note (kind=longrun): stage → accepted, 2 h TTL ──┘
     ◀── task notes every N s: "Denoise 7/20 (35%) — 260s [denoise]"
     ◀── task note: done → MP4 artifact
caller ◀── result: artifact reference to the video
```

Without the lease, a 10-minute render races the 300 s claim TTL: the
handler finishes after the relay already gave the stage up — result
discarded (the T-213 failure). The lease decouples *how long the work
takes* from *how long the claim lives*.

## What changes vs. the fast binary recipe

| | [wrap-local-binary](wrap-local-binary.md) (mflux) | this recipe (video.gen.native) |
|---|---|---|
| profile | plain | + `long_run: true`, `timeout` = worst case (3 h), `max_parallel: 1` |
| handler | blocking subprocess | subprocess **in background** + a watcher loop |
| progress | none | task notes: one `kind=longrun` at start, `progress` notes from live output |
| result | artifact | same — the ladder does not change |

## Steps

### 1. Profile — the flag plus honest ceilings

```yaml
- name: video.gen.native
  version: "2.0.0"
  type: tool
  claimable: true
  handler: /Users/<user>/.relay/handlers/video-gen-h3c.sh
  long_run: true            # T-154: lease instead of the 300 s claim timeout
  max_parallel: 1           # one model instance — queue, do not OOM
  timeout: 10800            # hard ceiling (3 h); the lease floor covers the
                            # in-between case, the hard limit ends runaways
```

### 2. Handler — start note, background process, watcher loop

The real deployment is a bash handler (~200 lines); its structure:

**a. Start note → stage becomes `accepted`:**

```bash
send_note() {   # kind: longrun | progress | info — task id from env vars
  curl -s -X POST "${RELAY_BASE}/relay/v2/scheduler/tasks/${TASK_ID}/notes" \
       -H "Authorization: Bearer ${RELAY_TOKEN}" \
       -d "{\"text\": \"$1\", \"kind\": \"$2\"}" > /dev/null
}
send_note "started: ${WIDTH}x${HEIGHT}, ${STEPS} steps, ~${EST_MIN} min" "longrun"
```

The `kind=longrun` note is what flips the stage into the long-run lease
state — without it the flag alone does not keep the claim.

**b. Run the binary in the background, watch its output:**

```bash
h3 --prompt "$PROMPT" … > "$H3_OUT" 2> "$H3_STDERR" &
H3_PID=$!
```

**c. The watcher loop — progress + keepalive in one place.** Poll the
process's stderr for the model's own progress lines and mirror them into
task notes every N seconds:

```bash
while kill -0 "$H3_PID" 2>/dev/null; do
  STEP=$(grep -oE 'denoise +[0-9]+/[0-9]+' "$H3_STDERR" | tail -1)
  PHASE=$(grep -oE 'text encoder|denoise|VAE|FFmpeg' "$H3_STDERR" | tail -1)
  send_note "Denoise ${STEP} (${ELAPSED}s) [${PHASE:-working}]" "progress"
  sleep 30
done
```

Two details worth stealing from the live handler:

- **Parse the model's own output, don't reinvent progress.** h3.c prints
  `denoise X/N` and phase names to stderr — the watcher greps them. Zero
  instrumentation of the binary.
- **A hard time limit kills runaways.** The watcher checks elapsed time
  against a max and aborts with an `info` note — a hung render should end
  as a failed task, not an eternal accepted one.

### 3. Result — unchanged

The MP4 leaves via `hp put` exactly like the PNG in
[wrap a local binary](wrap-local-binary.md): artifact envelope in the
result envelope, caller downloads with `artifact get`. Long work, same
return path.

### 4. Probe

```console
$ iowap-cli capabilities validate && iowap-cli capabilities publish
$ iowap-cli task submit --name video-smoke \
    --stage 'video.gen.native:{"prompt":"a red fox hacker, cyberpunk","steps":5}' \
    --owner <your-node-id>
$ iowap-cli task notes <task_id>     # watch the progress stream while it renders
$ iowap-cli task wait <task_id>
```

## The CPU-batch sibling: `storage.archive`

Same recipe with nothing to watch: a packing job has no stderr progress,
so the handler just appends a note per completed sub-step (`"packing
/dir-1 … done"`) — enough to hold the lease and give the caller a live
view. `timeout: 300` plus `long_run: true` is a valid combination: the
timeout bounds the handler process, the lease floor protects the claim.

## When you need this recipe

- The model takes minutes per invocation (video, large OCR batches, big
  transcriptions).
- The caller is an agent: notes are *its* visibility — an agent watching
  `task notes` can narrate progress to a human mid-run.
- Work is queue-shaped: `max_parallel: 1` + long_run turns the node into
  a serialized render queue without any queue infrastructure.
