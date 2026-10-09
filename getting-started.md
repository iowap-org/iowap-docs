# Getting Started

Pick the scenario that describes you — each one links the pages you need,
in order.

## 1. I just want to run a node

```bash
git clone https://github.com/iowap-org/iowap-node.git && cd iowap-node
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
node-cli relay set --server-url http://<relay>:8788
node-cli node register <relay>:8788 --name my-node
# approve in the dashboard, then:
node-cli capabilities validate default && node-cli capabilities publish default
node-cli daemon foreground
```

Full walkthrough: [node setup](node/setup.md). Next stops:
[operations](node/operations.md) (daemon as a service),
[capabilities how-to](node/capabilities.md) (own capabilities).

## 2. I want a relay + one node (single host)

1. [server setup](server/setup.md) — install, session secret, master seed,
   start
2. Bootstrap the first admin: [dashboard](server/dashboard.md)
3. Run a node on the same host: [node setup](node/setup.md)
4. Approve it: [dashboard → Nodes](server/dashboard.md)

## 3. I want a multi-node cluster

Relay first: [server setup](server/setup.md). Then one
[node setup](node/setup.md) per host. For a NAS storage node:
[storage](storage/storage.md) + [QNAP](storage/qnap.md). Node status
control (`busy`/`idle`): [operations](node/operations.md).

## 4. I write a client against the API

Start with the [API reference](reference/api.md) (auth → register →
heartbeat → claim → complete); the "Register a node" worked example there
shows how to grab a first token. Watch progress on the
SSE stream.
The `node-cli` is itself an API client — [CLI reference](node/cli.md).

## 5. I want to build a capability / handler

Model first: [capabilities](concepts/capabilities.md). Then:
[capabilities how-to](node/capabilities.md) (profiles) →
[handler contract](node/handlers/contract.md) (envelope I/O) →
[handler primitives](node/handlers/primitives.md) (file transfer,
complete-by-script). If your capability moves files:
[artifacts](concepts/artifacts.md).

## 6. I want to drive the fleet from my AI agent's desktop app

[Hermes integration](node/integrations/hermes.md) — chip, fleet pane, task
submission, live tracking.

## 7. I want Home Automation to join the cluster

[Home Assistant node](node/integrations/home-assistant.md) — HAOS app +
integration, capability matrix, `iowap.submit_task` from automations.

## 8. I want to understand the system first

[What is the relay](concepts/overview.md) →
[nodes](concepts/nodes.md) → [capabilities](concepts/capabilities.md) →
[tasks](concepts/tasks.md) → [tokens](concepts/tokens.md) →
[security](concepts/security.md). The [glossary](concepts/glossary.md)
defines every term used in these docs.

## Quick decision tree

| You want… | Read |
|-----------|------|
| Run the relay | [server setup](server/setup.md) (source) · [docker](server/docker.md) (container) · [QNAP storage](storage/qnap.md) (NAS node) |
| Run a node | [node setup](node/setup.md) |
| Write a capability | [capabilities how-to](node/capabilities.md) + [handler contract](node/handlers/contract.md) |
| Automate via HA | [home assistant node](node/integrations/home-assistant.md) |
| Script the API | [API reference](reference/api.md) |
| Read one page on everything | [overview](concepts/overview.md) |

## Operating a running cluster

| Task | Page |
|------|------|
| Approve nodes, users, recovery | [admin](server/admin.md) / [dashboard](server/dashboard.md) |
| Node status, daemon service | [operations](node/operations.md) |
| Token refresh/recovery | [token operations](node/tokens.md) |
| Database choice / backups | [server database](server/database.md) |
| Watch the cluster | [observability](concepts/observability.md) |
| Troubleshoot the CLI | [CLI reference](node/cli.md) |