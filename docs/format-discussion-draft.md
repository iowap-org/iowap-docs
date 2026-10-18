# README-Format iowap-org — Diskussionsvorlage (6 Punkte, Empfehlungen v2)

Stand 2026-10-18. Zweck: Entscheidung über die 6 offenen Punkte zum
einheitlichen README-Format über alle 12 iowap-org-Repos. Basis:
verifizierte Befundmatrix (t_08fa047f), Entscheidungsvorlage
(t_3d22a036), Devil's-Advocate-Gegenpositionen (t_63775060),
Vorschlag v1; Empfehlungen auf v2 nach DA-Prüfung (P4 zu A gekippt,
lychee- und Konflikt-Regeln in P6 übernommen). Noch nichts
umgesetzt: keine Repo-Änderungen, keine Commits; diese Datei liegt
uncommitted und gilt zugleich als Regelprobe — Prosa ≤80, Fences
mit Sprache, Pipes `| --- |`.

## Kurzkontext

Ziel ist ein Skelett für alle 12 READMEs: `# reponame` (lowercase) →
Tagline → Status (nur bei WIP) → `Why` → `Quick start` (Variante als
H3; jeder Schritt = Befehl + `# Expect`-Response-Shape +
Credential-Herkunft + Gate) → `Configuration` (env-Tabelle) →
`Architecture` (Diagramm, echte Hosts CT 106 / Mac mini / LXC 903) →
`Components/Layout` (repo-abhängig) → `Docs` (fixer iowap-docs-Pfad)
→ `License`. Das meta-Repo iowap behält zusätzlich `Position` +
`Repos`. Dazu die Maschine: `.markdownlint.jsonc` +
docs-validate-Workflow in jedem Repo. Heute lintet effektiv nur
iowap — ohne Konfig-File und ohne npm-Pin, der Regelsatz flottiert.

Status quo: Vorschlag v1 liegt vor, die 6 unten stehenden Punkte
sind offen. Der 17.10-Inventar-Befund wurde am 18.10. gegen den Code
verifiziert und dabei in 4 von 5 Punkten korrigiert — die Matrix
unten ist die gültige Datenbasis, nicht der 17.10-Stand.

## Verifizierte Befunde (Messung 2026-10-18, main @ HEAD)

12 Repos, lokale Clones, alle auf Branch `main`, strikt read-only.
Legende: ✅ erfüllt · ⚠️ teilweise · ❌ fehlt. Spalten (b)–(f)
weichen teils vom 17.10-Befund ab — Deltas stehen in der eigenen
Tabelle unten.

| Repo | (a) H1-Case | (b) Quickstart-Heading | (c) iowap-docs-Link | (d) Fence offen | (e) `.markdownlint.jsonc` | (f) docs-validate-WF | (g) Zeilen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iowap (meta) | UPPER `IOWAP` | ✅ `## Quick Start` | ⚠️ ja, kein Docs-Abschnitt | 0/3 | ❌ | ✅ markdownlint + lychee | 188 |
| client-mcp | lower | ❌ `## Install` | ❌ fehlt | 0/3 | ❌ | ❌ keine Workflows | 91 |
| docker | Title | ✅ `## Quick start` | ⚠️ ja, kein Docs-Abschnitt | 0/6 | ❌ | ❌ nur build/sync-WFs | 118 |
| docs | Title | ❌ `## Find your path` | ⚠️ Selbst-Link | 1/1 | ❌ | ❌ docs-ci ohne lint/lychee | 101 |
| federation | lower | ❌ `## Install & run` | ❌ fehlt | 2/6 | ❌ | ❌ | 128 |
| flow | lower | ❌ keine Einsteigsektion | ❌ fehlt | 0/0 | ❌ | ❌ nur publish | 41 |
| ha | mixed `for` | ❌ `## Installation` | ❌ fehlt | 1/2 | ❌ | ❌ | 173 |
| hermes-integration | Title | ❌ `## Install` (2×) | ❌ fehlt | 2/7 | ❌ | ❌ keine Workflows | 139 |
| node | lower | ✅ `## Quick Start (Linux)` | ✅ `## Docs` (6 Links) | 1/7 | ❌ | ❌ nur build-wheel | 130 |
| paperless | lower | ❌ `## Deploy (CT 106, …)` | ❌ nur Plaintext-Name | 0/2 | ❌ | ❌ | 83 |
| server | lower | ✅ `## Quick Start (Linux)` | ✅ `## Docs` (7 Links) | 1/5 | ❌ | ❌ | 121 |
| storage | lower | ✅ `## Quick Start (manual)` | ✅ `## Docs` (3 Links) | 0/3 | ❌ | ❌ | 74 |

Spalte (d): offene Fences ohne Sprachangabe gegen Fences gesamt;
alle Bare-Fence-Zeilen sind im Kontext geprüft (ASCII-Diagramme,
Trees, ein JSON-Beispiel). Spalte (c) zählt Markdown-Links und bare
URLs mit `iowap-docs`; Plaintext-Nennungen ohne URL (paperless L57)
zählen nicht als Link. flow hat überhaupt keine Code-Fences (0/0).

### Deltas zum 17.10-Befund (1 von 5 Claims bestätigt, 4 korrigiert)

| Metrik | 17.10-Befund | Verifiziert 18.10. |
| --- | --- | --- |
| (a) H1-Case | gemischt | bestätigt: 7 lower · 3 Title · 1 UPPER · 1 mixed |
| (b) Quickstart | 6 Varianten | 4 literale Formen in 5/12; 8 Einsteigs-Namen gesamt |
| (c) Docs-Link | fehlt 2/12 | fehlt 6/12 — neu: client-mcp, flow, ha, hermes-integration |
| (d) Bare Fences | 11/12 | 6/12 — docs, federation, ha, hermes-integration, node, server |
| (e) Lint-Config | fehlt 10/12 | fehlt 12/12 — nie in einer Git-History |
| (f) Lint-Workflow | fehlt 10/12 | fehlt 11/12 — nur iowap; docs hat CI ohne markdownlint |

### Zusatz-Befunde für die 6 Punkte

- Lint-Test mit der v1-Konfig (MD013 aus, MD041 aus, MD055/MD060
  leading+trailing): ohne Umbauten sind 9/12 Repos rot, 18 Fehler —
  MD040 bare Fences 8×, MD047 fehlendes Trailing-Newline 4×, MD036
  fette Tagline 4×, MD038 1×, MD033 1×. MD055/MD060: 0 Verstöße.
- Zeilenlänge: 30 Prosa-Zeilen >100 in 6 Repos, davon 23 Link-Zeilen
  (18 GitHub-docs-Links, 5 Badges) und nur 7 echte Prosa; 52
  Prosa-Zeilen >80 in 9 Repos.
- Link-Exposure: 85 externe Links, 77 (91 %) auf github.com. Der
  einzige laufende lychee-Job (iowap) hat ein GITHUB_TOKEN, aber
  keine Retries und keine localhost-Excludes (Spuren in server und
  paperless brauchen `--exclude`) — 4 der letzten 5 Läufe failure.
- 4/12 READMEs ohne Trailing-Newline am EOF: client-mcp, docker,
  docs, hermes-integration (MD047).
- `.markdownlint.jsonc` existierte nie in irgendeiner Git-History;
  der iowap-Workflow lintet ohne `-c` und ohne npm-Version-Pin.
- Konfliktfenster: iowap-ha hat einen offenen README-berührenden
  Task T-222 (HACS → Marketplace, PR an HA-core, changes requested);
  federation steht in aktiver T-094/T-105-Phase.
- README-Größen: 41 Zeilen (flow) bis 173 (ha); flow ist ein
  41-Zeilen-Stumpf (Intro + License) — eine Skelett-Existenz-Pflicht
  trifft ihn hart.

## Die 6 offenen Punkte

Je Punkt: Entscheidungsfrage, Optionen mit Vor-/Nachteil und
Aufwand, Empfehlung der Vorlage, Gegenposition des Devil's Advocate,
leeres Feld für die Entscheidung. Empfehlung heißt nicht entschieden
— erst wird entschieden, dann umgesetzt.

### P1 — Status: Blockquote oder `## Status`-Sektion?

Frage: Blockquote als Standard, `## Status`-Sektion nur für
tabellarischen Inhalt — oder der Sektion überall den Vorzug?

Option A — Blockquote pur (v1-Skelett): einzeilig nach der Tagline,
nur bei WIP, sonst weggelassen.

- Pro: schmales Skelett; das Flag steht vor `Why` — lesbar für
  Mensch und Agent.
- Contra: federation verliert seine Phase-Tabelle (echter Inhalt,
  T-094 bis T-105); hermes-integration muss Release-Prosa umziehen.
- Aufwand: 2 Repos, je unter 15 min — Inhalt wird neu geschichtet,
  nicht nur umbenannt.

Option B — `## Status`-Sektion generell.

- Pro: keine Formkollision für die federation-Tabelle.
- Contra: Mini-Repos (flow: allein `## License`) bekommen
  Skelett-Ballast für einen Status, den sie nicht führen.
- Aufwand: 0 Repos ändern sich, aber 12 Repos tragen eine Regel für
  etwas, das 10 gar nicht nutzen.

Option C — Hybrid mit fixer Position (Empfehlung): Blockquote ist
der Default-Slot (nach der Tagline, max. eine Zeile, nur bei WIP);
eine `## Status`-Sektion ist erlaubt, wenn der Inhalt tabellarisch
ist; Position fix: nach `Why`, vor `Quick start`.

```markdown
# iowap-federation

Federated discovery + HTTP transport for iowap nodes.

> **Status:** WIP — phases T-104/T-105 open

## Why

(...)

## Status

| Phase | Scope | Tasks | Status |
| --- | --- | --- | --- |
| 22 | Federation V1 | T-094-105 | in progress |
```

- Pro: federation und hermes-integration bleiben unangetastet; beide
  Formen sind fest sortiert — das Skelett bleibt deterministisch.
- Contra: zwei Formen = zwei Regelfälle; abmildern über das harte
  Kriterium „tabellarisch ja/nein“.
- Aufwand: 0 Repos, nur Regeltext.

Empfehlung der Vorlage: C. Begründung: In 10/12 Repos ist Status ein
Flag, in 2 Repos Inhalt; eine Regel, die beide Formen an fixen
Slots erlaubt, ändert kein heutiges README und verhindert trotzdem
Drift.

Gegenposition (Devil's Advocate): Der Angriff trifft nicht die
Hybrid-Form — fixe Slots sind gut —, sondern die Existenz-Pflicht
des v1-Skeletts drumrum: Mini-Repos (flow 41 Zeilen, allein
`## License`; client-mcp 91) können Sektionen nicht füllen, ohne
Boilerplate zu erfinden. Und „tabellarisch ja/nein“ ist subjektiv —
Grenzfälle (Changelog-Liste?) werden zur zweiten Regel-Doku.
Plan-Änderung: Skelett als fixe Reihenfolge mit Auslassungsregel
(weglassen statt mit `n/a` füllen); Pflicht nur für Tagline + Why +
Docs + License; Status bleibt Hybrid an den fixen Slots. Bevorzugt,
wenn Agent-Konsum der Existenz keine Extraktion braucht (kein Parser
zählt H2s) — „explizit leer“ erzwingt Goodhart-Boilerplate, das
Agenten als Inhalt fehllesen.

→ Ronnys Entscheidung: ____________

### P2 — H1-Case: lowercase Repo-Name oder menschlicher Titel?

Frage: H1 immer = Repo-Name lowercase — oder menschliche Titel für
user-nahe Repos? Betroffen: 5 Repos.

| Repo | heute | v1-Ziel |
| --- | --- | --- |
| iowap | `# IOWAP` | `# iowap` |
| docker | `# IOWAP Docker` | `# iowap-docker` |
| docs | `# IOWAP Documentation` | `# iowap-docs` |
| ha | `# IOWAP for Home Assistant` | `# iowap-ha` |
| hermes-integration | `# IOWAP Hermes Integration` | `# iowap-hermes-integration` |

Option A — lowercase Repo-Name (v1-Regel; Empfehlung).

- Pro: H1 = Repo-Name = Suchbarkeit; die Tagline trägt den
  Menschen-Namen; stabile Eingabe für llms.txt und Agent-Konsum.
- Contra: ha und docker liegen user-näher, ein Titel liest sich
  freundlicher.
- Aufwand: 5 Zeilen, ein PR, 10 min.

Option B — Ausnahmen für ha/docker (Zweiklassen-Regel).

- Pro: weniger Bruch im Lesefluss der End-User-Repos.
- Contra: genau der Heading-Stil-Mix, den v1 killen will; „wann
  gilt welcher Fall“ wird zur zweiten Regel-Doku.
- Aufwand: 0, aber das Regeldetail bleibt für immer.

Option C — gar kein H1 (GitHub rendert den Repo-Namen ohnehin).

- Pro: nichts zu pflegen.
- Contra: docs ist AI-Konsum-Ziel (Page-contract, llms.txt); ohne
  H1 verliert der Export den Titelkontext.

Empfehlung der Vorlage: A. Begründung: Der Repo-Name ist die einzige
stabile ID über 12 Repos; alles Menschliche gehört in Tagline und
Docs-Page. Nebenbefund: GitHub baut den Page-Titel ohnehin aus
Repo-Name + Description — lowercase verschenkt nichts Sichtbares.

Gegenposition (Devil's Advocate): Die Regel selbst ist robust — der
einzige Einwand ist die Reihenfolge: iowap-ha hat einen offenen
Migrations-Task (T-222), der den Install-Teil des ha-README ohnehin
ändert. Plan-Änderung: kein separater 5-Zeilen-H1-Patch — die
H1-Änderung wandert in den ha-PR von T-222 oder in den je-Repo-
Format-PR direkt danach; für die übrigen 4 Repos gilt: Teil des
je-Repo-PRs (P6-B), nie ein eigenes PR. Bevorzugt: immer — es geht
nur um die Koppelung, nicht um die Regel.

→ Ronnys Entscheidung: ____________

### P3 — `Why` als fixer Name vs. bestehende Namen?

Frage: `Why` als fixer H2-Name für alle — oder ein anderer bzw.
freier Name? Heute: server `Features`, ha `What it does`, client-mcp
`The problem`/`The answer`, node `What You Can Build`.

Option A — `Why` fix (v1-Skelett; Empfehlung).

- Pro: erzwingt Problem-first mit ehrlicher Grenze (Problem /
  Ansatz / bewusst nicht kann); fixe Namen sind der Preis des
  Skeletts — der Heading-Stil-Mix war der Drift-Beweis.
- Contra: `Why` liest sich abstrakter als `What it does`.
- Aufwand: 4 Repos — server (Liste zu Bullets schichten), ha
  (Umbenennung + Straffung), node (Umbenennung + Angleichung),
  client-mcp (zwei Überschriften zusammenlegen).

Option B — `What it does` fix.

- Pro: federation und ha müssten nichts ändern.
- Contra: lädt zur Feature-Liste ein; die ehrliche Grenze
  (v1-Kriterium) hat darin keinen Platz.
- Aufwand: 4 Repos in umgekehrter Richtung, gleiche Menge.

Option C — Name frei, nur Aufbau-Pflicht (Problem/Ansatz/Grenze).

- Pro: 0 Umbenennungen heute.
- Contra: ohne fixen Namen ist die Struktur-Pflicht review-only und
  driftet wieder — derselbe Mechanismus wie beim Quickstart-Stil.

Empfehlung der Vorlage: A. Begründung: Ein Name, der die Struktur
erzwingt, schützt nachhaltiger als ein Struktur-Kriterium ohne
Namen; `Why` ist kurz, unmissverständlich und passt zur
Lesereihenfolge des Skeletts (erst das Warum, dann wie es läuft).

Gegenposition (Devil's Advocate): Der Beweis ist schwächer als
behauptet — die verifizierte Matrix zählt 4 literale
Quickstart-Formen (2 unterscheiden sich nur im Case), nicht 6
Varianten; freie
Namen haben also weniger driftiert, als die Vorlage erzählt. Und
„server Liste zu Bullets schichten“ ist keine Namens-, sondern eine
inhaltliche Umschichtung: Ein Format-PR, der nur `## Why` über einen
`## Features`-Block schreibt, produziert ein Heading, das seinen
Inhalt bricht — der Name regelt den Inhalt nicht. Plan-Änderung:
Migration zweistufig — Stufe 1 (Format-PR) benennt Headings und
legt das 3-Bullet-Skelett als Vorlage hinter die alte Prosa; Stufe 2
(Inhalt-Rewrite, server und node zuerst) ist ein separater kleiner
Task je Repo. Bevorzugt, wenn Agent-Konsum Priorität hat (fixe
Namen = deterministische Extraktion); ohne diesen Bedarf wäre
Option B billiger.

→ Ronnys Entscheidung: ____________

### P4 — MD013: Konvention 80 ohne lint oder lint mit Länge?

Frage: Zeilenlänge als Konvention ohne lint (v1-Konfig) — oder
MD013 mit lint, und dann bei welcher Länge? Zahlen: 30 Prosa-Zeilen
>100 in 6 Repos, davon 23 Link- und 5 Badge-Zeilen (nur 7 echte
Prosa); 52 Zeilen >80 in 9 Repos.

Option A — MD013 aus, 80 als Konvention (v1-Konfig); optional
`.editorconfig` mit `max_line_length = 80` als Editor-Hinweis.

```jsonc
{ "MD013": false }
```

- Pro: 0 Migration; Review oder Editor-Wrap trägt die Regel.
- Contra: mechanisch ungeschützt; der 17.10-Zustand (143 Zeilen
  über 80 in 11 Repos) ist genau das Ergebnis dieses Modus.
- Aufwand: 0.

Option B — MD013 lint @ 100, Tabellen/Code ausgenommen (ehemalige
v1-Empfehlung, in der Prüfung gekippt).

```jsonc
{
  "MD013": {
    "line_length": 100,
    "tables": false,
    "code_blocks": false
  },
  "MD041": false,
  "MD055": { "style": "leading_and_trailing" },
  "MD060": { "style": "leading_and_trailing" },
  "MD033": { "allowed_elements": ["br", "kbd"] }
}
```

- Pro: fängt grobe Verletzungen (lange unumbrüchliche URLs,
  Copy-Paste-Reste), ohne die Prosa-80-Zucht zu erzwingen; 80
  bleibt Konvention.
  Migration 30 Zeilen in 6 Repos — liegt im P6-Rewrite-Pfad.
- Contra: zwei Zahlen (80 Konvention, 100 lint) müssen dokumentiert
  sein; lint schützt die 80 nicht.
- Aufwand: 30 Zeilen, im Rewrite-Pfad, kein Zusatz-PR.

Option C — MD013 lint @ 80, Tabellen/Code ausgenommen.

```jsonc
{ "MD013": { "line_length": 80, "tables": false, "code_blocks": false } }
```

- Pro: Konvention wird mechanisch; Zustand sofort sauber.
- Contra: 52 Prosa-Zeilen in 9 Repos umbrechen (server 19, node 10,
  storage 8); Umbrechen von Prosa erzeugt Diff-Rauschen bei jedem
  Folge-Edit — die spürbarste Migration der drei Varianten.

Empfehlung der Vorlage: A (v2, gekippt von B nach DA-Prüfung).
Begründung: 23 der 30 Prosa-Zeilen >100 sind unumbrüchliche
Link-Zeilen (18 GitHub-docs-Links, 5 Badges) — MD013 kann URLs
nicht ausnehmen; MD013@100 trägt 0 der 18 heutigen Lint-Fehler und
verrechnet sich um Faktor 4. Der mechanische Wert der lint-Konfig
liegt vollständig bei MD040/MD047/MD036/MD033. 80 bleibt Konvention,
`.editorconfig` mit `max_line_length = 80` als Editor-Hilfe. B nur,
wenn Ronny nachweisbar will, dass neue >100-Zeilen inkl. URLs rot
schlagen — dann sind vorher Badge-Zeilen und reference-style-Links
zu klären, sonst ist B das schlechteste der drei Optionen.

Gegenposition (Devil's Advocate, mit Zahl): Von den 30 Zeilen >100
sind 77 % Link-Zeilen — MD013 kann URLs nicht ausnehmen, Link-URLs
sind unumbrüchlich. Die Optionen für diese 23 Zeilen sind
reference-style-Links (Style-Zwang), kürzere Ankertexte (Inhalt
weg) oder 23 per-line-Disable-Kommentare (Noise): Empfehlung B
verrechnet sich damit um Faktor 4, und MD013 trägt zudem 0 der 18
heutigen Lint-Fehler. Neben Lint @ 100 stirbt die
Prosa-80-Konvention, weil zwischen 80 und 100 alles erlaubt ist.
Plan-Änderung: P4 auf A drehen (MD013 aus, 80 Konvention +
`.editorconfig` 80); der mechanische Wert der lint-Konfig liegt
vollständig bei
MD040/MD047/MD036/MD033. Unabhängig von der Wahl lintet der
iowap-Workflow ohne Konfig-File und ohne npm-Version-Pin — der
Regelsatz flottiert; belegt durch Fix-Commits wie „wrap line 41 …
80-character line limit“ (die Zeile hat heute 76 Zeichen) und 7
README-Zeilen >80 bei CI-grün — der Rollout muss diesen Workflow
nivellieren, sonst bestehen ab Tag 1 zwei Standards. B ist
vorzuziehen, wenn Ronny nachweisbar will, dass neue >100-Zeilen auch
URLs rot schlagen — dann sind vorher zwei Antworten fällig: Was
passiert mit Badge-Zeilen (die v1-Badges-Regel sagt über Bestand
nichts) und mit reference-style-Links? Ohne diese Antworten ist B
das schlechteste der drei Optionen.

→ Ronnys Entscheidung: ____________

### P5 — Single Source of Truth: Skelett in iowap-docs?

Frage: Skelett + Pflichtregeln als Seite in iowap-docs committen —
und wohin genau?

Option A — `reference/format.md` als eigene Page (Empfehlung).

- Pro: echte SoT, lintet selbst mit, landet im llms.txt-Export und
  ist für Agent-Konsum adressierbar; passt in die docs-Struktur
  (reference/ existiert — ein `docs/`-Subdir gibt es dort nicht;
  das v1-Papier meinte mit „docs/format.md“ das docs-Repo selbst).
- Contra: neue Pflege-Pflicht; wer das Format ändert, muss die Page
  und 12 lint-Konfigs im Blick behalten.
- Aufwand: 1 PR in iowap-docs; die Seite ist das v1-Papier plus
  Snippets.

Option B — Anhang an die Page-contract-Page.

- Pro: ein Ort weniger.
- Contra: Page-contract ist der Autoren-Kontrakt für docs-Pages;
  die README-Format-Norm ist ein anderes Thema, die Page wächst
  über 100 Zeilen hinaus.

Option C — kein Commit; Format lebt im Skill iowap-repo-docs und im
Board-Attachment.

- Pro: keine Pflegestelle im Repo.
- Contra: kein Human- und AI-Konsumpfad über das docs-Portal; SoT
  hängt an einem lokalen Skill-Verzeichnis.

Empfehlung der Vorlage: A, plus Verweis: die Page-contract-Page
linkt auf `reference/format.md` als die Norm für READMEs.

Gegenposition (Devil's Advocate): Der versprochene Drift-Schutz —
„Format-Änderungen nur als docs-PR, zusammen mit der lint-Konfig
(doc und Maschine im selben Commit)“ — ist mechanisch unmöglich:
heute existiert 0 Konfig (nie in Git-History), und nach dem Rollout
liegen 12 Kopien in 12 Repos, die ein docs-Commit nicht mitziehen
kann. Der erste Repo mit vergessener Konfig ist der Drift — genau
das, was P5 verhindern will. Plan-Änderung: Version-Pin je Konfig
(`"format-version": "1"` direkt im `.markdownlint.jsonc`), der
docs-validate-Workflow greppt den Pin gegen den aktuellen Wert aus
`reference/format.md` und failt bei Mismatch — 3 Zeilen YAML, die
Drift vom Review-Problem zum CI-Fehler machen. Später alternativ:
Konfig-SoT in iowap-docs + Sync-Skript (Querschnitt Q1). Bevorzugt,
wenn Konfig-Änderungen selten bleiben (historische Rate: nie) — der
Pin reicht; der Sync lohnt ab der ersten Feintuning-Welle.

→ Ronnys Entscheidung: ____________

### P6 — Rollout: Reihenfolge und meta-Timing

Frage: zuerst lint-Konfig + Workflow flächig, oder zuerst README-
Umbauten — und meta zuerst oder zuletzt? Der Zahlenvergleich steht
in der Tabelle im Abschnitt „Rollout-Vergleich“.

Option A — Konfig + Workflow zuerst (v1-Plan), dann Umbauten.

- Pro: Schienen liegen, bevor der Verkehr kommt.
- Contra: die v1-Konfig ist heute in 9/12 Repos rot (18 Fehler);
  flächige Einführung heißt 9 rote README-Pipelines bis die Umbauten
  durch sind — oder eine Non-Blocking-Phase, die man später scharf
  stellen muss.
- Aufwand: 12 Konfigs + 10 Workflows + 18 Fehlerfixes, verteilt
  über zwei Wellen.

Option B — je Repo ein Commit: Konfig + Workflow + README-Umbau im
selben PR (Empfehlung).

- Pro: jedes Repo bleibt grün — kein CI-Lärm, kein roter Zustand im
  Board; Repo für Repo abhaken (validate, publish).
- Contra: 12 kleine PRs statt 2 Wellen; die Konfig wird 12× kopiert
  (Template liegt vor, mechanisch).
- Aufwand: je Repo 30–60 min, gesamt ein Arbeitstag-Segment.
- Pilot-Empfehlung: iowap-paperless — mit der v1-Konfig bereits
  grün, kleines README, klarer Deploy-Kern (CT 106).
- meta zuletzt: meta ist das komplexeste README (Position +
  Repos-Tabelle, 3 Prosa-Zeilen >100) und profitiert am Ende davon,
  dass die Regeln durch 11 Repos stabilisiert sind; die Repos-
  Tabelle braucht nur Links, keine Format-Beispiele.

Option C — Hybrid: Welle 1 Konfig + Workflow non-blocking flächig,
Welle 2 je Repo Umbau + Blocking.

- Pro: Maschine ist sofort überall an.
- Contra: jedes Repo wird zweimal angefasst; Welle 2 macht Welle 1
  teilweise rückgängig.

Gegenposition (Devil's Advocate): Die je-Repo-Idee (Repos bleiben
grün) ist richtig — aber zwei blinde Flecken fehlen. (1) Lychee: 85
externe Links, 91 % auf github.com; der laufende lychee-Job hat ein
GITHUB_TOKEN, aber keine Retries und keine localhost-Excludes,
läuft über `**/*.md` — 4 von 5 letzten Läufen rot. Für die
localhost-Spuren in server und paperless braucht lychee
`--exclude`. 11 Repos
bekommen diesen Workflow NEU, und der Plan hat keinen Abschnitt
lychee-Konfig.
(2) Reihenfolge: „Pilot paperless“ sortiert nicht nach
Konfliktgefahr — iowap-ha (T-222 offen, changes requested) und
federation
(T-104/T-105 aktiv) stehen auf der Umbau-Liste; ein Format-PR dort
konkurriert mit laufender Arbeit. Die v1-Welle 1 (ausgerechnet ha,
federation, hermes-integration zuerst) invertiert das Risiko
schlimmstens. Plan-Änderung: lychee-Config zuerst ins Template;
Sortier-Regel „kein Format-PR in ein Repo mit offenem
README-berührenden Task“; Wellen nach Konfliktarmut (Tabelle und
Details im
Abschnitt „Rollout-Vergleich“). Bevorzugt: blocking erst nach einer
Non-Blocking-Phase mit beobachteter Fehlerrate nahe null.

→ Ronnys Entscheidung: ____________

## Rollout-Vergleich (Detail zu P6)

Varianten der Sequenz:

| Variante | Aufwand | Risiko |
| --- | --- | --- |
| A: Konfig + Workflow zuerst | 12 Konfigs + 10 Workflows + 18 Fehlerfixes, 2 Wellen | 9 rote Pipelines bis der Umbau durch ist; oder Non-Blocking, später scharf stellen |
| B: je Repo ein Commit | 12 kleine PRs, je 30–60 min (~1 Tag gesamt) | Repos grün; 12× Handkopier; lychee-Risiko ungedeckt ohne Zusätze |
| C: Hybrid (non-blocking zuerst) | Welle 1 flächig + Welle 2 je Repo | jedes Repo 2× angefasst; Welle 2 macht Welle 1 teils rückgängig |

meta-Timing:

| Variante | Aufwand | Risiko |
| --- | --- | --- |
| meta zuerst | identisch | komplexstes README zuerst — Muster-PR auf instabilem Regelsatz |
| meta zuletzt (Empf.) | identisch | Regeln durch 11 Repos stabilisiert; Repos-Tabelle braucht nur Links |

Devil's-Advocate-Bedingungen zu Variante B:

- lychee-Config zuerst ins Template: GITHUB_TOKEN, `--max-retries 3`,
  `--exclude localhost`/`127.0.0.1`, 2 Wochen `continue-on-error` —
  dann scharf stellen.
- Sortier-Regel: kein Format-PR in ein Repo mit offenem
  README-berührenden Task — ha erst nach T-222, federation nach
  T-105.
- Wellen nach Konfliktarmut: paperless → flow/docker/docs →
  server/node/storage (mit P4/P3-Stufe 1) →
  federation/hermes-integration/client-mcp → ha → meta.

## Entscheidungs-Checkliste

- [ ] P1 Status: Hybrid — Blockquote default, `## Status` nur bei
  tabellarischem Inhalt, Position nach `Why` (C). DA-Zusatz:
  Skelett als Reihenfolge mit Auslassungsregel, Pflicht nur
  Tagline/Why/Docs/License.
- [ ] P2 H1: lowercase Repo-Name in allen 12, Tagline trägt den
  Menschen-Namen (A). DA-Zusatz: ha-Fix in den T-222-PR bzw.
  je-Repo-PR koppeln, nie ein separates H1-PR.
- [ ] P3 Why: `Why` fix in allen 12 (A). DA-Zusatz: Migration
  zweistufig — Rename im Format-PR, Inhalt-Rewrite (server, node)
  als eigener Mini-Task.
- [ ] P4 MD013: Empfehlung v2 = A — MD013 aus lint, 80 Konvention,
  `.editorconfig` (`max_line_length = 80`); 23/30 Zeilen >100 sind
  unumbrüchliche Link-Zeilen, MD013 trägt 0 der 18 heutigen Fehler.
  B (lint @ 100) nur bei explizitem Wunsch, >100-Zeilen inkl. URLs
  rot zu schlagen — dann vorher Badge- und reference-style-Frage.
- [ ] P5 SoT: `reference/format.md` in iowap-docs, Page-contract
  verlinkt (A). DA-Zusatz: format-version-Pin je Konfig +
  Workflow-grep gegen die Page.
- [ ] P6 Rollout: je Repo ein Commit, Pilot paperless, meta zuletzt
  (B) mit DA-Bedingungen als Teil der Empfehlung: lychee-Config
  ins Template (Retries + localhost-Excludes, 2 Wochen
  continue-on-error), kein Format-PR bei offenem README-Task,
  Wellen nach Konfliktarmut (Details im Rollout-Vergleich).
- [ ] Q1 Konfig-Verteilung: kein README-Generator (Why-Prosa nicht
  generierbar, GitHub rendert keine Includes); Konfig + Workflow
  per einmaligem Sync-Skript statt 12× Handkopieren. Vertagbar
  (der format-version-Pin reicht); Sync lohnt ab mehr als einer
  Konfig-Änderung pro Quartal.

Diese Datei liegt bewusst uncommitted in `~/projects/iowap-docs/docs/`
— die SoT-Entscheidung (P5) steht aus; erst danach wird ein Ort im
Repo (oder außerhalb) festgelegt und committet.
