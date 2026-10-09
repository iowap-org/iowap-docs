# IOWAP Documentation

Setup guides, concepts, API reference, and node documentation for the
[IOWAP](https://github.com/iowap-org/iowap) ecosystem — everything needed
to run a relay, connect a node, or build capabilities.

## Find your path

| I want to… | Start here |
|------------|-----------|
| Run a node | [getting-started §1](getting-started.md) → [node/setup](node/setup.md) |
| Run a relay server | [getting-started §2](getting-started.md) → [server/setup](server/setup.md) (source) · [server/docker](server/docker.md) (container) |
| Understand the system | [concepts/overview](concepts/overview.md) |
| Build a capability / handler | [concepts/capabilities](concepts/capabilities.md) → [node/capabilities](node/capabilities.md) → [node/handlers/contract](node/handlers/contract.md) |
| Automate my home | [node/integrations/home-assistant](node/integrations/home-assistant.md) |
| Drive the fleet from an agent desktop | [node/integrations/hermes](node/integrations/hermes.md) |
| Script against the API | [reference/api](reference/api.md) |
| Look up a term | [concepts/glossary](concepts/glossary.md) |

## Structure

```
getting-started.md            # Scenario-based entry point (8 reader paths)
concepts/                     # WHY/WAS — one page per model term
├── overview.md               #   What the relay is, positioning
├── nodes.md                  #   Node model, heartbeat, statuses
├── capabilities.md           #   Routing keys, naming, ladder
├── tasks.md                  #   Task/stage lifecycle, status system
├── tokens.md                 #   Credential families
├── artifacts.md              #   Transfer ladder (inline/artifact/bridge)
├── observability.md          #   /health /ready /metrics, logs
├── security.md               #   Boundary model
└── glossary.md               #   Verbatim terminology (page titles bind to it)
server/                       # Relay operations
├── setup.md  admin.md  dashboard.md  docker.md  database.md
node/                         # Node operations + framework
├── setup.md  operations.md  config.md  tokens.md  capabilities.md  cli.md
├── handlers/                 #   contract.md (envelope I/O), primitives.md (hp put/get)
└── integrations/             #   home-assistant.md, hermes.md
federation/                   # Planned multi-relay bridging — not implemented
└── concept.md
storage/                      # NAS storage node
├── storage.md  qnap.md
reference/                    # Look-up material
├── api.md                    #   Endpoint reference (openapi.json = machine source)
├── database-backends.md      #   DB layer internals, adding a backend
└── design-board.md           #   Historical design records
```

## Page-contract (for writers & AI consumers)

Every page is human-readable **and** machine-predictable:

- Reserved section skeletons per page type: Concepts use
  `What it is / How it works / What it is NOT / Related pages`; ops pages
  use numbered Steps + `Verification` + `Troubleshooting`. Section names
  are stable anchors.
- Titles use [glossary](concepts/glossary.md) terms — one vocabulary for
  humans and machines.
- Commands: one command per code block with expected output as `# -> `
  comments.
- Status quo only — no task ids or phase numbers; history lives in git
  and the boards. Not-implemented features live only in
  `federation/` and clearly marked boxes.
- New pages must be added to `llms.txt` (see
  [CONTRIBUTING](CONTRIBUTING.md)).

This documentation is served live by every relay at
`/relay/v2/docs/` (index: `/relay/v2/docs`) — slugs are stable:
path relative to `docs/`, `/` joined with `-`.

## Repos

| Area | Repo |
|------|------|
| Meta + integration guide | [iowap-org/iowap](https://github.com/iowap-org/iowap) |
| Relay Server | [iowap-org/iowap-server](https://github.com/iowap-org/iowap-server) |
| Node Framework | [iowap-org/iowap-node](https://github.com/iowap-org/iowap-node) |
| Storage Node | [iowap-org/iowap-storage](https://github.com/iowap-org/iowap-storage) |
| Docker Images | [iowap-org/iowap-docker](https://github.com/iowap-org/iowap-docker) |
| Hermes Integration | [iowap-org/iowap-hermes-integration](https://github.com/iowap-org/iowap-hermes-integration) |

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — the page-contract, style rules,
and the pre-commit checks.