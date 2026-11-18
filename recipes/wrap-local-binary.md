# Recipe: Wrap a Local Binary (and Return Files)

> End state: a capability that runs a model binary on one specific machine —
> where its weights live — and returns the generated file through the
> relay. Reference deployment: `image.generate.mflux` (FLUX.2 Klein via
> mflux, Apple silicon, artifact upload) — alongside `fm.chat` (Apple's
> on-device FM), `doc.convert` (LibreOffice), and the whole `video.gen.*`
> family.

## What you'll end up with

```text
caller ── task submit image.generate.mflux:{prompt} ──▶ relay ──▶ the node with the model
                                                                handler: subprocess run
                                                                uploads PNG via hp put
caller ◀── result: artifact reference (download, artifact get) ┘
```

The machine keeps its special role (GPU/NPU, weights, licensing) — the
fabric just makes it reachable by name.

## Ingredients

- The node that hosts the binary, iowap-node ≥ 2.3.44
- The binary itself plus whatever it needs (weights cached, venv activated)
- ~50 lines of handler

## Steps

### 1. Handler — subprocess, artifact upload, clean envelope

```python
#!/usr/bin/env python3
"""image.generate.mflux — FLUX.2 Klein via mflux, output as artifact.

Payload: {"prompt": str, "steps": int (optional), "width"/"height": int (optional)}
Result: result envelope with an __iowap_ref__ artifact reference to the PNG.
"""
import json, os, subprocess, sys, tempfile, uuid

MFLUX   = os.environ.get("MFLUX_BIN", "mflux")   # on PATH inside the node venv
STEPS   = int(os.environ.get("MFLUX_DEFAULT_STEPS", "4"))

def main() -> int:
    payload = json.load(sys.stdin)
    prompt = payload.get("prompt")
    if not prompt:
        print("prompt missing", file=sys.stderr); return 1
    steps = int(payload.get("steps", STEPS))
    w, h = int(payload.get("width", 1024)), int(payload.get("height", 1024))

    out = os.path.join(tempfile.gettempdir(), f"mflux_{uuid.uuid4().hex}.png")
    run = subprocess.run(
        [MFLUX, "--prompt", prompt, "--steps", str(steps),
         "--width", str(w), "--height", str(h), "--output", out],
        capture_output=True, text=True, timeout=600)

    if run.returncode != 0 or not os.path.isfile(out):
        print(f"mflux failed: {run.stderr[-400:]}", file=sys.stderr); return 1

    # hp put prints a transfer envelope; it picks the smallest rung that
    # fits (inline ≤ 5 MB, artifact ≤ 50 MB) and handles auth itself.
    put = subprocess.run(
        ["iowap-cli", "hp", "put", out, "--cap", "image.generate.mflux"],
        capture_output=True, text=True)
    if put.returncode != 0:
        print(f"artifact upload failed: {put.stderr}", file=sys.stderr); return 1

    envelope = json.loads(put.stdout)
    print(json.dumps({"status": "ok",
                      "result": {"image": envelope, "prompt": prompt,
                                 "steps": steps}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

What earns this its own recipe (vs. the HTTP one):

- **`hp put` replaces all transport logic.** The handler never base64s,
  never uploads by hand, never sees the token — the CLI primitive builds
  the `__iowap_ref__` envelope and picks the ladder rung
  ([primitives](../node/handlers/primitives.md),
  [artifacts](../concepts/artifacts.md)).
- **The caller downloads symmetrically.** A caller receives the envelope
  in the task result and resolves it with `iowap-cli artifact get` (or
  `hp get` from its own handler code).
- **Timeout math.** Handler `timeout` in the profile must exceed the
  subprocess timeout, which must exceed the model's worst case. Generating
  hangs otherwise show up as killed stages, not clean failures.

### 2. Capability profile

```yaml
- name: image.generate.mflux
  version: 1.1.0
  claimable: true
  handler: /home/<user>/.relay/handlers/mflux-handler.py
  max_parallel: 1              # one model instance — queue instead of OOM
  timeout: 660
  type: tool
  upload_modes: [inline, artifact]
  description: 'Image generation with mflux (FLUX.2 Klein 4B q8). Parameter:
    prompt (required), steps (optional), width/height (optional). Returns an
    artifact reference to the PNG.'
  input_schema:
    fields:
      prompt:
        name: prompt
        type: string
        required: true
        description: 'Image description. Example: a red fox on a snowy roof,
          watercolor style'
      steps:
        name: steps
        type: integer
        required: false
        description: 'Sampling steps. Example: 4'
```

### 3. Publish + 4. Probe

```console
$ iowap-cli capabilities validate && iowap-cli capabilities publish
$ iowap-cli task submit --name mflux-smoke \
    --stage 'image.generate.mflux:{"prompt":"a red fox on a snowy roof","steps":4}' \
    --owner <your-node-id>
$ iowap-cli artifact get <artifact_id> --output /tmp/fox.png
```

The PNG opens, the round trip is proven.

## Variations

- **On-device model APIs** (`fm.chat`, `fm.ocr`): same recipe, the
  subprocess is `/usr/bin/fm respond …` and the result is usually text —
  no artifact needed.
- **Document conversion** (`doc.convert`): the subprocess is
  `libreoffice --headless --convert-to pdf`; input arrives *as* an
  envelope (`hp get` resolves it first), output leaves as one. Both
  directions of the ladder in one handler.
- **Video** (`video.gen.native`): identical shape, `max_parallel: 1` and a
  generous `timeout` matter even more — minutes per clip, RAM-bounded.
- **No binary, only a big local file?** That is not a capability — put the
  file on a storage node and hand out `storage_ref`s; capabilities wrap
  computation, not content (see [artifacts](../concepts/artifacts.md)).
