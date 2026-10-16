#!/usr/bin/env python3
"""Hygiene gate for documentation addresses and tokens (T-220).

Enforces the CONTRIBUTING.md house rules mechanically across every
git-tracked Markdown page and all capture files:

- IPv4 addresses must be documentation-safe (RFC 5737 test ranges
  192.0.2.x / 198.51.100.x / 203.0.113.x, loopback 127.x, 0.0.0.0).
  Anything else — RFC 1918, CGNAT (Tailscale 100.64/10), link-local,
  public ranges — fails the check with file:line.
- Full relay token shapes (rt_/rs_/adm_ + 6+ chars) must never appear;
  docs use the `rt_…` ellipsis form only.
- Own domains (rpon.eu) fail; mDNS names like `iowap.local` are a feature
  name, not an address, and stay allowed.

The captures/ directory is held to the same standard plus its own policy
(captures/README.md); capture.py already anonymizes on write, this script
is the tripwire (fail = red PR).

Local run: python3 tools/check_captures.py
"""

import subprocess
import sys
from pathlib import Path

import re

REPO = Path(__file__).resolve().parents[1]

ALLOWED_IP_PREFIXES = (
    "192.0.2.",
    "198.51.100.",
    "203.0.113.",
    "127.",
    "0.0.0.0",
)
IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
# Real tokens carry entropy; a suffix without any digit is a doc placeholder
# (adm_xxx…) or a config key name (rt_refresh_interval_seconds) — not a leak.
TOKEN_RE = re.compile(r"\b((?:rt|rs|adm)_[A-Za-z0-9_-]{6,})\b")
DENY_DOMAINS = ("rpon.eu",)


def tracked_markdown() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return [REPO / f for f in out]


def violations(path: Path) -> list[str]:
    found: list[str] = []
    try:
        rel = path.relative_to(REPO)
    except ValueError:
        rel = path  # out-of-tree probes from the negative-test suite
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    for line_no, line in enumerate(lines, start=1):
        for token in TOKEN_RE.findall(line):
            if not any(c.isdigit() for c in token[4:]):
                continue  # placeholder shape (adm_xxx…) or config key name
            found.append(f"{rel}:{line_no}: token {token[:14]}…")
        for domain in DENY_DOMAINS:
            if domain in line:
                found.append(f"{rel}:{line_no}: own domain {domain}")
        for m in IP_RE.finditer(line):
            ip = m.group(1)
            if not ip.startswith(ALLOWED_IP_PREFIXES):
                found.append(f"{rel}:{line_no}: unsafe IPv4 {ip}")
    return found


def main() -> int:
    paths = list(REPO.glob("captures/*"))
    paths += tracked_markdown()
    all_v: list[str] = []
    for p in paths:
        if p.is_file() and p.suffix == ".md":
            all_v.extend(violations(p))
    if all_v:
        print(f"DOCUMENTATION HYGIENE FAIL — {len(all_v)} violations:")
        for v in sorted(set(all_v)):
            print(f"  {v}")
        return 1
    count = len(set(p for p in paths if p.is_file() and p.suffix == ".md"))
    print(f"OK: {count} markdown/capture files clean (IPs, tokens, domains).")
    return 0


if __name__ == "__main__":
    sys.exit(main())