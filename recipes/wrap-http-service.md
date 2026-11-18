# Recipe: Wrap an HTTP Service

> End state: a capability that turns any HTTP-speaking service — local or
> remote — into something every agent in the fabric can call by name.
> Reference deployment: `stt.ai` and `tts.ai` (whisper-1 and tts-1 behind an
> OpenAI-compatible speech server) plus the REST+token pair `paperless.*`.

## What you'll end up with

```text
caller (any node) ── task submit stt.ai:{audio_ref} ──▶ relay ──▶ your node
                                                                handler: HTTP POST
                                                                to the service
caller ◀── result: {"text": "…"} ──────────────────────────────┘
```

The service itself stays exactly as it is — no plugin, no SDK, no restart.
The capability is a thin mapping between the task payload and the service
API.

## Ingredients

- A node that can reach the service (same host is ideal: no extra auth surface)
- The service's endpoint + auth (env var, never hardcoded)
- iowap-node ≥ 2.3.44 on that node
- ~40 lines of handler

## Steps

### 1. Handler — map payload → HTTP call → result

```python
#!/usr/bin/env python3
"""stt.ai — Speech-to-Text via the local speech server (whisper-1).

Reads the stage payload on stdin, posts the audio file to an
OpenAI-compatible /audio/transcriptions endpoint, prints the result
envelope on stdout.
"""
import json, os, sys, urllib.request, uuid

ENDPOINT = os.environ["STT_ENDPOINT"]          # http://127.0.0.1:8090/v1/audio/transcriptions
TIMEOUT  = int(os.environ.get("STT_TIMEOUT", "120"))

def main() -> int:
    payload = json.load(sys.stdin)             # the stage payload
    audio = payload.get("audio")               # path to a local file
    if not audio or not os.path.isfile(audio):
        print("audio file missing", file=sys.stderr); return 1

    boundary = uuid.uuid4().hex
    model = payload.get("model", "whisper-1")
    body = []
    for name, value in (("model", model), ("response_format", "json")):
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.bin"\r\n'
                f'Content-Type: application/octet-stream\r\n\r\n'.encode())
    with open(audio, "rb") as fh:
        body.append(fh.read())
    body.append(f'\r\n--{boundary}--\r\n'.encode())

    req = urllib.request.Request(ENDPOINT, data=b"".join(body), method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = json.load(resp).get("text", "")

    print(json.dumps({"status": "ok", "result": {"text": text, "model": model}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Two contract details that matter:

- **stdin → payload, stdout → result envelope** (`{"status", "result"}`) —
  normative: [handler contract](../node/handlers/contract.md).
- **Credentials via env, never in the profile file.** A service token
  (`PAPERLESS_TOKEN`-style) lives in the node's service environment; the
  handler reads it with `os.environ`.

### 2. Capability profile

Append to your node profile (`~/.relay/profiles.d/<profile>.yaml`):

```yaml
- name: stt.ai
  version: 1.0.0
  claimable: true
  handler: /home/<user>/.relay/handlers/stt-handler.py
  max_parallel: 2
  timeout: 150                  # above the handler's own TIMEOUT
  type: tool
  description: 'Speech-to-Text via whisper-1. Parameter: audio (required,
    local file path), model (optional, default whisper-1).'
  input_schema:
    fields:
      audio:
        name: audio
        type: string
        required: true
        description: 'Path to a local audio file. Example: /tmp/voicenote.m4a'
      model:
        name: model
        type: string
        required: false
        description: 'Whisper model name. Example: whisper-1'
```

### 3. Publish

```console
$ iowap-cli capabilities validate
$ iowap-cli capabilities publish
```

The node heartbeats the capability; the relay matches `stt.ai` from any
caller within seconds.

### 4. Probe — one real task

```console
$ iowap-cli task submit --name stt-smoke \
    --stage 'stt.ai:{"audio":"/tmp/voicenote.m4a"}' --owner <your-node-id>
$ iowap-cli task wait <task_id>
```

A transcript in the result is the proof. If the service is down, the
handler's non-zero exit + stderr line becomes a clean `failed` task — not a
hung stage.

## Variations

- **REST + token service** (`paperless.search`): same shape, but the
  handler adds an `Authorization: Token …` header from the env var and
  maps pagination/tags. Read-only services are the easiest first
  capability.
- **TTS is the mirror image** (`tts.ai`): the *result* is a file, so the
  handler writes the synthesized audio to a temp path and returns it via
  `hp put` — see [wrap a local binary](wrap-local-binary.md) for the
  artifact side of that pattern.
- **Two instances of the same service** (a GPU box and a CPU fallback):
  register both nodes with the same capability name; the relay picks by
  load. That is the whole scaling story.
