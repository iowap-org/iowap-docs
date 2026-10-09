# VERIFICATION — Docs-Review iowap-docs 34b067c (Felix, eigene Nachprüfung)

Stand: 2026-10-04 · Gegenstück: STATUS.md (code-reviewer-Profil) · Probe-HOMEs unter
`~/.hermes/cache/scratch/finding-a-probe*` (Live-Config nie angefasst).

## Finding A — `relay set --discover` auf registrierten Nodes: stiller No-Op (MINOR→Doc-Wahrheit / Design-Glitch) ✅ reproduziert

- Doku-Claim (node/cli-reference.md §relay): "`--discover` … removes the pin
  and re-enables mDNS discovery." + setup.md-Unterabschnitt: "the node then
  discovers the relay over mDNS on every fallback."
- Code: `node register` persistiert `base_url` im **State-File**
  (nodes/common/cli/cli_server.py:98, 100 — `save_meta`).
  Auflösung: `cfg.base_url or **meta.base_url**` sonst Discovery
  (nodes/common/relay_client.py:163-165). `relay set --discover` poppt aber
  NUR `relay_config.json` (relay_client.py:297) — Meta-Pin bleibt.
- **Probe (isoliertes Scratch-HOME, 2026-10-04):**
  1. meta=`{"base_url": "http://10.99.0.1:8788"}`, cfg-Werte normal →
     `_base_url()` → `http://10.99.0.1:8788` (Meta gewinnt, wie im Code).
  2. Nach `relay set --discover` (Probe-Aufruf von `_cmd_relay_set`, argv-äquivalent):
     cfg hat kein `base_url` mehr, CLI-Output behauptet "discovery enabled" —
     `_base_url()` löst TROTZDEM `http://10.99.0.1:8788` auf.
  3. Ohne `meta.base_url` schlägt Discovery an (Probe: `mDNS discovery
     unavailable (zeroconf not installed)` — Beweis, dass der Discovery-Pfad
     betreten wird, im Live-Netz also aktiv).
- **Urteil:** Doku-Versprechen auf jedem Standard-Node (via `node register`
  registriert) wahrheitswidrig. Fix-Empfehlung: **Code** (Root-Fix):
  `_cmd_relay_set` soll bei `--discover` auch `meta["base_url"]` entfernen;
  Doku bleibt dann wahr. Skill-Regel: Code bauen, dass die Doku stimmt.
- Was der Fix NICHT löst: `node register` schreibt weiter einen Meta-Pin
  (gut: Sicherheit First-Run); Discovery bleibt explizites Opt-in.

## Finding B — Doku-Exit-Codes unvollständig: exit 2 fehlt (MINOR)

- Code: `_cmd_relay_set` → `SystemExit(2)` bei falscher/fehlender.Flag-Kombi
  (relay_client.py:284-289). Doku-Tabelle (cli-reference.md §relay) listet
  nur 0/1. Tabelle ergänzen: `2 | Usage error (--server-url und --discover
  zusammen, bzw. beides fehlt)`.
- Übrige Sektions-Konvention: route-Sektion listet auch nur 0/1 — aber dort
  existiert kein Exit-2-Pfad; hier schon. Korrektur erwiesen nötig.

## Finding C — `--json` wird von `relay set/discover` nicht gelesen (COSMETIC/MINOR)

- Global-Parser hat `--json` (node_cli.py:762), `cli_server._cmd_node_register`
  implementiert es (cli_server.py:103), aber `_cmd_relay_set`/`_cmd_relay_discover`
  lesen `args.json` nirgends (relay_client.py:278-319 — grep-frei bestätigt).
- Doku-Claim fehlt (ich habe nichts über `--json` behauptet) → **keine**
  Doku-Lüge, aber Konventions-Loch (T-077: "alle relevanten commands").
  Empfehlung: Issue-Holding, kein Doc-Edit nötig; falls implementiert, dann
  auch dokumentieren.

## Finding D — server/setup.md §11: `mdns_service_name`-Key fehlt (MINOR, anderes Repo)

- Server-Config real: ~/projects/iowap-server/config.py:19-21
  (`mdns_service_name: str = "IOWAP Relay Service"`).
- Docs §11-Beispiel (server/setup.md:ff387) listet nur `enable_mdns` +
  `mdns_hostname`. §11 sagt "all common options" — der live entscheidende
  Key fehlt. Server-Doku-Fix gehört ins iowap-server-Doku-Thema (separates
  Repo), meine §relay-Verlinkung auf §11 bleibt korrekt (enable_mdns wird
  dort ja dokumentiert).

## Finding E — Wortwahl "dumb" in public docs (COSMETIC, pre-existing)

- node/handler-contract.md:172: "The relay server stays a **dumb
  pass-through**" — ist NICHT Teil von 34b067c (Stand davor), Policy verlangt
  public-docs-English ohne "dumb". Benennung als Adjacent-Finding; Fix
  optional (z.B. "an unopinionated pass-through" / "stores stage.result
  verbatim, without parsing").

## Version/Task-Deckung

- Wheel 2.3.16: `pip show iowap-node` = 2.3.16 == pyproject == GitHub
  Release wheel-v2.3.16 (Latest). Doc-Claims "since 2.3.16" konform.
- TASKS.md T-187-Row auf done gezogen (04a9c79 / be1e81a / 34b067c, Live-Verify,
  Negativ-Test) — Backup: TASKS.md.bak-20261004.
- Task-ID-Zuordnung handler-contract.md "T-166": bezieht sich auf den
  Envelope-Unwrap-Fix aus der T-166-Bridge-Session (f897351,
  tests/test_t166_find_result_envelope.py, 5 Tests grün lokal). Die
  T-166-Board-Row (Bridge, done 2026-10-03) deckt den Kontext ab — der
  Envelope-Sub-Fix war aus der Bridge-Live-Smoke-Session entstanden und wird
  im Task-Text der T-166-Row nicht namentlich geführt → **Task-Update
  nötig** (T-166-Row um den Envelope-Sub-Fix ergänzen), sonst löst die
  Doc-Referenz "T-166" für Board-Leser auf die Bridge-Tätigkeit auf und der
  Envelope-Fix hat keine Task-Verankerung.

## Probe-Artefakte

- `~/.hermes/cache/scratch/finding-a-probe/.relay/` (Case registrierter Node)
- `~/.hermes/cache/scratch/finding-a-probe-nometa/.relay/` (ohne Meta-Pin)
- Probe-Skript inline (execute_code), gegen `~/projects/iowap-node` CWD,
  isolierte `HOME`s, kein Live-Config-Zugriff.