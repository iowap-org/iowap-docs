# IOWAP Documentation

**Setup guides, concepts, API reference, and node documentation for the IOWAP ecosystem.**

---

## Structure

```
├── concepts.md              # Core concepts — capabilities, tasks, relay model
├── getting-started.md       # First steps — set up a server, register a node
├── server/                  # Relay server documentation
│   ├── setup.md             #   Server installation & configuration
│   ├── docker.md            #   Docker deployment
│   ├── dashboard.md         #   Dashboard usage guide
│   └── admin.md             #   Administration & user management
├── node/                    # Node framework documentation
│   ├── setup.md             #   Node installation & registration
│   ├── cli-reference.md     #   Full CLI reference
│   ├── node-config.md       #   node.yaml configuration
│   ├── node-daemon.md       #   Daemon operation & service management
│   ├── capabilities.md      #   Capability definition reference
│   ├── capability-concept.md#   Capability matching model
│   ├── concept.md           #   Node architecture deep-dive
│   ├── ssn.md               #   SSN proxy & capability pages
│   ├── federation.md        #   Federation (peer-to-peer relay bridging)
│   └── token-lifecycle.md   #   Token auth flow
├── storage/                 # Storage node documentation
│   ├── qnap-storage-node.md #   QNAP-specific deployment
│   └── storage.md           #   Storage capabilities & bridge mode
└── reference/               # Reference documentation
    ├── api.md               #   Full API reference
    ├── database-backends.md #   SQLite & PostgreSQL backends
    └── design-board.md      #   Architecture decisions & design history
```

## About

This repo contains all documentation for the [IOWAP](https://github.com/iowap-org/iowap) ecosystem — everything you need to set up a relay server, run a node, or build your own capabilities.

| Area | Code Repo |
|------|-----------|
| Relay Server | [iowap-org/iowap-server](https://github.com/iowap-org/iowap-server) |
| Node Framework | [iowap-org/iowap-node](https://github.com/iowap-org/iowap-node) |
| Storage Node | [iowap-org/iowap-storage](https://github.com/iowap-org/iowap-storage) |
| Meta | [iowap-org/iowap](https://github.com/iowap-org/iowap) |

## License

AGPL-3.0