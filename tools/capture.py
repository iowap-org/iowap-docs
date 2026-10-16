#!/usr/bin/env python3
"""Capture real relay output as documentation source material (T-220).

CONTRIBUTING.md: "Values come from real captures, never invented." This tool
runs the same commands the docs quote against the live relay (through
node-cli, which owns relay auth/target), anonymizes the output via
tools/_anonymize.py, and stores it with provenance in captures/.

The relay is only called read-only (health probe, list views).

Usage (docs repo checkout on a machine with node-cli + node state):
    python3 tools/capture.py                 # health, node list, capabilities
    python3 tools/capture.py --metrics       # + relay metrics (can be long)

Output:
    captures/health-YYYYMMDD.md   (node-cli server health — /health + /ready)
    captures/nodes-YYYYMMDD.md    (node-cli node list)
    captures/capabilities-YYYYMMDD.md (node-cli capabilities server)
    captures/metrics-YYYYMMDD.md  (node-cli server metrics, if requested)
"""

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from _anonymize import anonymize_text  # noqa: E402

COMMANDS = {
    "health": ["server", "health"],
    "nodes": ["node", "list"],
    "capabilities": ["capabilities", "server"],
    "metrics": ["server", "metrics"],
}


def resolve_node_cli() -> str:
    """PATH first, then the ~/.relay/node.yaml self-stamp pin (T-226)."""
    import shutil

    found = shutil.which("node-cli")
    if found:
        return found
    pin_file = Path.home() / ".relay" / "node.yaml"
    if pin_file.exists():
        m = next(
            (
                l[13:] for l in pin_file.read_text().splitlines()
                if l.startswith("node_cli_path:")
            ),
            None,
        )
        if m and Path(m.strip()).exists():
            return m.strip()
    raise SystemExit(
        "node-cli not found (PATH and ~/.relay/node.yaml pin). Install iowap-node."
    )


def run(name: str, argv: list[str]) -> str:
    proc = subprocess.run(
        [resolve_node_cli(), *argv],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise SystemExit(f"{name}: node-cli exited {proc.returncode}: {proc.stderr[:400]}")
    return proc.stdout


def write_capture(slug: str, argv: list[str], raw: str) -> Path:
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    out = REPO / "captures" / f"{slug}-{today}.md"
    out.write_text(
        f"# {slug} — real capture\n\n"
        f"captured_at: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"command: `node-cli {' '.join(argv)}`\n"
        f"anonymized: IPs RFC 5737, tokens redacted, own domains example.com\n\n"
        f"```\n{anonymize_text(raw).rstrip()}\n```\n",
        encoding="utf-8",
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--metrics", action="store_true", help="also capture relay metrics")
    args = parser.parse_args()

    slugs = ["health", "nodes", "capabilities"] + (["metrics"] if args.metrics else [])
    (REPO / "captures").mkdir(exist_ok=True)
    for slug in slugs:
        argv = COMMANDS[slug]
        path = write_capture(slug, argv, run(slug, argv))
        print(f"wrote {path.relative_to(REPO)} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())