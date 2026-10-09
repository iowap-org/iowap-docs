#!/usr/bin/env python3
"""Check relative markdown links + llms.txt entries resolve to existing files.

Run from the repo root:  python tools/check_links.py
Exit 0 = all good, 1 = broken links found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]+\]\(([^)#]+?)(?:#[^)]*)?\)")


def main() -> int:
    broken: list[str] = []
    checked = 0
    for md in list(ROOT.rglob("*.md")):
        if ("legacy" in md.parts or ".hermes" in md.parts or ".git" in md.parts):
            continue
        text = md.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path = (md.parent / target).resolve()
            checked += 1
            if not path.exists():
                broken.append(f"{md.relative_to(ROOT)}: -> {target}")
    # llms.txt entries point at real pages
    llms = ROOT / "llms.txt"
    if llms.exists():
        for m in re.finditer(r"\((\S+?\.md)\)", llms.read_text(encoding="utf-8")):
            path = (ROOT / m.group(1)).resolve()
            checked += 1
            if not path.exists():
                broken.append(f"llms.txt: -> {m.group(1)}")
    for line in broken:
        print("BROKEN", line)
    print(f"{checked} internal links checked, {len(broken)} broken")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())