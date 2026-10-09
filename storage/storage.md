# Storage Node

The NAS-backed storage node — the cluster's durable file home. It is a
**service node** (role `service`, not `worker`). Python code:
[iowap-org/iowap-storage](https://github.com/iowap-org/iowap-storage)
(handlers, bridge server, retention watchdog); images/compose:
[iowap-org/iowap-docker](https://github.com/iowap-org/iowap-docker)
(`base/`, `storage/`). QNAP walkthrough: [qnap](qnap.md).

## What it is

A node offering file, folder, large-file, and backup capabilities.
Every handler enforces the path-traversal guard (`_safe_path`): every
caller-supplied path resolves inside the storage root and is rejected if
it escapes after symlink/`..` resolution.

## How it works

### Capabilities

| Capability | Claimable | Description |
|------------|-----------|-------------|
| `storage.store` | yes | Write a file: inline `data_base64`, artifact by id, or bridge via `storage_ref`; `action: store_as_is` (default) or `extract` for uploaded archives |
| `storage.fetch` | yes | Read back as `data_base64` (small) or bridge download channel (large) |
| `storage.delete` | yes | Remove a file or directory (recursive) |
| `storage.list` | yes | List files under a prefix |
| `storage.quota` | yes | Disk usage + threshold (`RELAY_STORAGE_QUOTA_THRESHOLD`, default 0.9) |
| `storage.stat` | yes | Stat a single path (size, mtime, is_dir) |
| `storage.move` | yes | Rename/move a file or directory |
| `storage.extract` | yes | Unpack a stored `.tar.gz` into a directory |
| `storage.archive` | yes | Pack a directory into a `.tar.gz` |
| `storage.upload_channel` | yes | Open a temp bridge route for streaming a large file **to** the NAS |
| `storage.download_channel` | yes | Open a temp bridge route for streaming a large file **from** the NAS |
| `backup.create` | yes | Versioned backup (full/incremental) with JSON manifest |
| `backup.list` | yes | List backups, filterable by `source`/`type` |
| `backup.info` | yes | Return one backup's manifest |
| `backup.restore` | yes | Return backup data (inline for small, bridge for large) |
| `backup.delete` | yes | Mark backup `deleted` (manifest kept for audit, data removed) |
| `backup.retention` | yes | Apply keep_last / max_age_days / GFS policy to a source |

### The bridge (large files)

The regular task path (returning `data_base64` in the result) would load
big files into RAM. Instead the node runs a small HTTP server alongside
the daemon — `bridge_server.py` (Starlette, port 8791, started by the
container entrypoint):

- `POST /upload/{channel_id}` — stream body → NAS
- `GET /download/{channel_id}` — stream NAS file → caller
- **Source-IP allowlist middleware:** every request's source IP is
  checked against the relay's IP (resolved once at startup from
  `RELAY_URL`; `RELAY_SERVER_IP` overrides). Non-matching → 403;
  unresolvable → fail-closed (403 everywhere).

```text
Caller                Relay (proxy)            Storage bridge server        NAS
  │  submit upload_channel  │                          │                    │
  │─────────────────────────>│                          │                    │
  │                        claim → handler registers temp route (/upload/ch_x)
  │                        handler completes {upload_url, channel_id, ttl}
  │<──── upload_url ────────│                          │                    │
  │  POST upload_url        │   stream body chunkwise  │  write chunkwise  │
  │─────────────────────────>│─────────────────────────>│───────────────────>│
  │<──── 200 ───────────────│<─────────────────────────│                    │
```

The relay proxy streams the request body and the upstream response
chunkwise — large files never sit fully in the relay's RAM. Same on the
way back (`storage.download_channel`).

This is the `bridge` rung of the cluster's transfer ladder
([concept: artifacts](../concepts/artifacts.md)) — the durable counterpart
to the relay's transient artifact store.

### Backups as versioned artifacts

No database index — each backup is a folder with a `manifest.json` +
`data.bin` under `<STORAGE_PATH>/backups/<backup_id>/` (`backup_id` =
`bk_<16-hex>`). `backup.create` supports `type: full` and `type:
incremental` (with `base_backup_id` referencing an existing backup).
`backup.retention` applies `{"keep_last": N}`, `{"max_age_days": N}`, or
GFS (`keep_daily/keep_weekly/keep_monthly`) — a background
retention watchdog applies configured policies periodically from
`~/.relay/retention.yaml` (env `RELAY_RETENTION_CONFIG`); an empty or
missing config means **no** automatic deletion (fail-safe).

### Folder transfer

Directories travel as a single `.tar.gz` over the bridge — the **uploader
decides** whether the node unpacks (that's `storage.store` with
`action: extract`, or `storage.extract` after the fact); the node stays
agnostic (no FUSE/mounting). Extraction rejects traversal entries
(`..`, absolute paths, symlinks) — an escaping archive fails the stage.

## Configuration

| Env | Default | Meaning |
|-----|---------|---------|
| `RELAY_STORAGE_PATH` | `/storage` | Storage root (set in the image) |
| `RELAY_SERVER_IP` | *(from RELAY_URL)* | Explicit bridge-allowlist relay IP — practically never needed |
| `RELAY_TRUST_FORWARDED_FOR` | `0` | Honour `X-Forwarded-For` only when the bridge sits behind a controlled L7 proxy; default trusts the socket peer only |
| `BRIDGE_PORT` | `8791` | Bridge server port |
| `RELAY_RETENTION_CONFIG` | `~/.relay/retention.yaml` | Retention policies for the watchdog |
| `RELAY_RETENTION_INTERVAL` | `3600` | Watchdog run interval (seconds) |

## What it is NOT

- **Not the relay's storage** — the artifact store on the relay is
  transient (TTL-purged); durable copies belong here.
- **Not an extractor by default** — archives are stored untouched unless
  the caller asks for extraction.
- **Not publicly exposed** — the bridge server accepts calls only from
  the relay, and only over routes the relay proxies.

## Related pages

- [qnap.md](qnap.md) — deployment on QNAP Container Station
- [transfer ladder](../concepts/artifacts.md) — where bridge fits
- [Docker](../server/docker.md) — server-side composition
- [iowap-storage repo](https://github.com/iowap-org/iowap-storage) — source