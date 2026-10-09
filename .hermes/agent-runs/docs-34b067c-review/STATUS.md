# STATUS — Docs-Review iowap-docs 34b067c

**Run:** hermes -p code-reviewer chat --oneshot --yolo -Q --max-turns 32
**Profil:** code-reviewer · **Session:** 20261004_100348_fe0eda
**Hinweis:** Run endete am Iterations-Limit (exit 1), Report wurde inline im
Prozess-Output abgeliefert und hier unverändert konserviert (Rescue durch
Felix). Keine Board-Tasks angelegt (wie vereinbart).

---

DOCS-REVIEW iowap-docs 34b067c — STATUS
Modus: read-only. Keine Edits. Reviewer.
Basis (verifiziert): iowap-docs HEAD 34b067c (clean); iowap-node HEAD be1e81a == origin/main == Wheel 2.3.16 (site-packages-Dateien relay_client/cli_bridge/cli_server/node_cli/node_utils byte-identisch zu main, diff -q leer). Release wheel-v2.3.16 Latest, publishedAt 2026-10-03T22:15:06Z. Tests: `test_t166_find_result_envelope.py` (5) + `test_t187_relay_discovery.py` (16) → 21 passed.

## FINDING 1 — blocker (Kern-Claim falsch)
"relay set --discover … re-enables mDNS discovery" ist bei via `node register` registrierten Nodes FALSCH: der alte Pin überlebt in `iowap-agent.json` und gewinnt gegen den gelöschten Config-Pin.

Belege:
- nodes/common/relay_client.py:297-298 — `--discover` macht nur `cfg.pop("base_url", None)` + `write_json_atomic(CONFIG_PATH, cfg)`. Es schreibt AUSSCHLIESSLICH `relay_config.json`, niemals das meta.
- nodes/common/relay_client.py:164 — `url = cfg.get("base_url") or meta.get("base_url")`. Nach dem Unpin ist `cfg` leer → Fallback auf `meta["base_url"]` → Discovery-Zweig (Z.167-173) wird nie erreicht.
- nodes/common/cli/cli_server.py:92-100 — `_cmd_node_register` schreibt `meta = {…, "base_url": base_url}` via `save_meta` (Z.100). Das ist der in node/setup.md:77 (§2) empfohlene Registrierungsweg.
- Live-Probe (read-only, Simulation): `_base_url({"base_url":"http://192.168.2.60:8788"}, {})` → liefert die meta-URL, Discovery-Aufrufe = 0; ohne meta-`base_url` → Discovery-Aufrufe = 1.

Betroffene Doc-Zeilen:
- node/cli-reference.md:1126 ("remove the pin and let the node find the relay via mDNS")
- node/cli-reference.md:1136 (Actions-Tabelle, `--discover`-Zeile)
- node/setup.md:57 ("the node then discovers the relay over mDNS on every fallback")

Warum die Tests das nicht decken: `test_relay_set_discover_clears_pin` (test_t187_relay_discovery.py:179) prüft nur `"base_url" not in data` in relay_config.json — `_cmd_relay_set` liest das meta gar nicht, der meta-Shadow-Pfad wird nirgends getestet. Grün ≠ korrekt (Silent-Deviation).

Severity: blocker. Empfehlung: entweder Code-Fix (`--discover` muss auch `meta["base_url"]` entfernen, sonst wirkt die Pin-Empfehlung asymmetrisch) ODER Doc ehrlich machen ("--discover entfernt den Pin in relay_config.json; ein base_url im Node-State (iowap-agent.json) aus `node register` überstimmt ihn weiterhin").
Was der reine Doku-Fix NICHT löst: den Code-Gap selbst (Unpin bleibt funktionslos auf `node register`-Nodes). Das ist upstream iowap-node, nicht Docs.

## FINDING 2 — minor (Exit-Code-Tabelle unvollständig)
Code kennt Exit 2 (Usage-Fehler), Doku nur 0/1.
- Live: `node-cli relay set` → rc=2; `node-cli relay set --server-url X --discover` → rc=2. Code: relay_client.py:282-283 (mutually exclusive), 285-286 (nothing to do), beide `raise SystemExit(2)`.
- node/cli-reference.md:1157-1162 nennt nur 0 und 1. Die Doku stellt `relay set` mit beiden Flags vor — die Kombination/Leerform ist also erreichbar und liefert 2.
Severity: minor. Empfehlung: Zeile "2 | Usage error: both/neither of --server-url/--discover" ergänzen.

## FINDING 3 — minor (T-ID-Kollision T-166)
"T-166" bedeutet im Docs-Repo bereits die Ephemeral-Bridge, jetzt zusätzlich den Envelope-Unwrap.
- Board ~/.hermes/projects/iowap-node/TASKS.md:6 — T-166 = "Ephemeral Bridge — file serve/get".
- node/handler-contract.md:131 — "(T-166, fixed in 2.3.16)" meint den Unwrap.
- Kein eigener Board-Row für den Unwrap-Fix; er wurde in die T-166-Bridge-Session absorbiert (commit f897351 "fix(t166): unwrap T-005b response envelope", tests/test_t166_find_result_envelope.py).
- Bereits vorhandene Bridge-Bedeutung derselben ID: node/handler-primitives.md:79,86; node/cli-reference.md:1474,1520-1521; concepts.md:426.
Severity: cosmetic–minor (Leser-Irritation, keine sachliche Falschaussage). Empfehlung: Note präzisieren, z.B. "T-166 follow-up fix (2.3.16 deploy session)" + Verweis, dass der Vertrag selbst T-005b ist (der Handler-Contract-Absatz führt T-005 korrekt: handler-contract.md:5).

## FINDING 4 — minor, in-diesem-Repo behebbar (nicht separates Repo!)
Server-Doku fehlt `mdns_service_name`, obwohl die neuen Node-Docs genau darauf verweisen.
- node/setup.md:65 und node/cli-reference.md:1152 sagen "enable `enable_mdns: true` (+ `mdns_service_name`)".
- server/setup.md:387-388 zeigt nur `enable_mdns: true` + `mdns_hostname: "iowap"` — kein `mdns_service_name`.
- Server-Code unterstützt ihn real: iowap-server/config.py:19-21 (`enable_mdns`, `mdns_hostname`, `mdns_service_name: str = "IOWAP Relay Service"`), core/zeroconf.py:9,67-69.
- KORREKTUR zur Auftragsannahme: server/*.md ist KEIN Submodule, sondern im selben Repo getrackt (`git ls-files server/` → 4 Blobs; kein .gitmodules). Der Fix ist also hier möglich (server/setup.md §11, 376).
Severity: minor (dangling instruction). Empfehlung: `mdns_service_name: "IOWAP Relay Service"` in §11-Beispiel ergänzen — im selben Repo, kein separates.

## FINDING 5 — info (Wortwahl "dumb", pre-existing)
- grep -rni "dumb" über iowap-docs: nur node/handler-contract.md:172. git blame → faffbb8 (T-005-Doc-Commit) → NICHT von 34b067c eingeführt, sondern vorbestehend.
- Eine schriftliche "Repo-Regel" dazu konnte ich im Repo nicht finden (kein CONTRIBUTING, keine Style-Datei).
Severity: info. Der neue Commit verstößt nicht; falls die Regel gilt, ist es ein Altbestand außerhalb des Review-Scopes.

## FINDING 6 — cosmetic (Konsistenz der neuen Abschnitte)
- Beispiel-IPs inkonsistent: node/cli-reference.md:1127 nutzt die reale Relay-IP 192.168.2.60, node/setup.md:55 nutzt 192.168.2.10.
- Anker-Inkonsistenz: node/setup.md:67 verlinkt mit `#11-configuration-reference`, node/cli-reference.md:1153 verlinkt im selben Commit ohne Anker (`../server/setup.md`). Ziel identisch.
Severity: cosmetic. Empfehlung: einheitliche Platzhalter-IP + einheitlicher Anker. (192.168.2.60 ist RFC1918, kein Secret — Sanitize-Hinweis, kein Blocker.)

## FINDING 7 — info (--json)
`relay set/discover` implementieren kein `--json` (Node-seitig: node_cli.py:762 ist der globale Flag; relay-Handler lesen `args.json` nicht). ABER die Global-options-Tabelle (node/cli-reference.md:29) listet relay NICHT in "Supported by:", d.h. die Doku über-claimt nichts → keine Inkonsistenz. Nebenbefund: `node-cli --json relay discover` wird akzeptiert und still ignoriert. Severity: info.

## VERIFIZIERT WAHR (kein Finding)
- Env-Präzedenz env > relay_config.json > Default: relay_client.py:189-197, DEFAULT_SERVICE_NAME Z.186 — deckt cli-reference.md:1143-1145/1550 und setup.md:62-63. ✓
- Avahi-Unescape: relay_client.py:268 `label.replace("\\032", " ")` (Laufzeit-String ist Backslash+032); Live-Probe: escaped Name "IOWAP\032Relay\032Service" matcht → unescape wirkt. ✓ (Doku-Aussage korrekt; der T-187-Testfile testet das Escape NICHT explizit.)
- Fallback ruft gefilterte Discovery: relay_client.py:167-173 in `_base_url`; zusätzlich file_serve.py:114-121 via Alias `_discover_relay_mdns` (relay_client.py:273-275). "on every fallback" ✓.
- Pin schaltet Discovery ab: relay_client.py:164-165 (nur `if not url`); test_base_url_prefers_pin_over_discovery ✓ — gilt für den Config-Pin (meta-Shadow siehe Finding 1).
- `relay discover`-Output: prints `http://<addr>:<port>` + (nur wenn KEIN `--name`) `  service: <name> (_http._tcp)` (relay_client.py:317-318), rc 0; not-found → rc 1, Z.313-316. Doku-Claim wahr; die zweite Zeile ist in keinem Beispiel abgedruckt (unvollständig, nicht falsch — cosmetic).
- Anker `#relay` → `## relay` (cli-reference.md:1122); Row Z.56; Titelstil konsistent mit `## route` (1038) / `## bridge` (1166). ✓
- Anker `../server/setup.md#11-configuration-reference` → "## 11. Configuration reference" (server/setup.md:376), GitHub-Anker korrekt. ✓
- handler-contract Discriminator-Wortlaut exakt wie cli_bridge.py:53-61 (`"_handler" in res or {"status","result","error"} <= set(res)`; error→None; flat passthrough). Note handler-contract.md:133-139 präzise. ✓
- test_t166_find_result_envelope.py: 5 Tests, Szenarien decken die Claims (unwrap / flat-legacy / non-envelope / error-envelope / no-completed-stage). ✓
- Versionen: pyproject 2.3.16, Wheel 2.3.16, "since 2.3.16" überall korrekt; grep "2\.3\.1[0-9]" → nur 2.3.16-Treffer, keine 2.3.14/2.3.15-Reste in den Docs. ✓
- Deutsch/Englisch: neue Inhalte durchgehend Englisch; Code-Fences `bash`/plain wie Repo-Konvention (42× bash, 91× plain). ✓
- Server-"With mDNS enabled (recommended)" (server/setup.md:153) vs Node-"Disabling discovery … recommended default" (cli-reference.md:1154): unterschiedliche Ebenen (Server advertiset vs Node-Discovery-Fallback) — als konsistent lesbar, kein Widerspruch. Empfehlung optional: kurzer Cross-Link. ✓

## FAZIT
Nur ein blocker (Finding 1: das Kernversprechen "--discover re-enablet Discovery" hält bei `node register`-Nodes nicht) — Rest minor/cosmetic/info. Der Commit ist inhaltlich überwiegend sauber, Anchor/Version/Contract-Claims halten der Gegenprüfung stand.