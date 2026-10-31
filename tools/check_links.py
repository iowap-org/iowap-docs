#!/usr/bin/env python3
"""Doc link gates: relative links resolve, llms.txt <-> pages both directions.

Run from the repo root:  python tools/check_links.py
Exit 0 = all good, 1 = broken links / llms.txt drift.

Forward:  links inside every page, and llms.txt entries, resolve to files.
Reverse:  every content page must be listed in llms.txt (entry drift catches
          pages that were added without their llms.txt line).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]+\]\(([^)#]+?)(?:#[^)]*)?\)")

# Meta/internal markdown: never required as llms.txt entries.
# Page trees (concepts, server, node, storage, flow, federation, clients,
# reference, docs, …) are NOT exempt on purpose: a page in any tree the
# reverse check sees must be listed in llms.txt.
EXEMPT_DIR_PARTS = {"legacy", "captures", "tools", ".github", ".git", ".hermes"}
EXEMPT_FILENAMES = {"README.md", "CONTRIBUTING.md"}
# Forward link walk keeps its historical exemption set (captures links stay
# checked); both now match tree-relative parts so a repo checkout nested
# under a same-named ancestor directory cannot blank the check.
FORWARD_SKIP_PARTS = {"legacy", ".git", ".hermes"}


def content_pages(root: Path) -> list[Path]:
    """Markdown pages that belong in llms.txt."""
    pages: list[Path] = []
    for md in root.rglob("*.md"):
        # tree-relative parts only — ancestor paths above the repo root
        # (e.g. a clone living under .../.hermes/... ) must not matter
        parts = md.relative_to(root).parts
        if any(part in EXEMPT_DIR_PARTS for part in parts):
            continue
        if md.name in EXEMPT_FILENAMES:
            continue
        pages.append(md)
    return pages


def main() -> int:
    broken: list[str] = []
    missing: list[str] = []
    checked = 0
    for md in list(ROOT.rglob("*.md")):
        if (any(p in FORWARD_SKIP_PARTS for p in md.relative_to(ROOT).parts)):
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
    # llms.txt entries point at real pages (forward), and every content page
    # is listed in llms.txt (reverse).
    llms = ROOT / "llms.txt"
    if llms.exists():
        text = llms.read_text(encoding="utf-8")
        listed: set[str] = set()
        for m in re.finditer(r"\((\S+?\.md)\)", text):
            listed.add(m.group(1))
            path = (ROOT / m.group(1)).resolve()
            checked += 1
            if not path.exists():
                broken.append(f"llms.txt: -> {m.group(1)}")
        for md in content_pages(ROOT):
            rel = md.relative_to(ROOT).as_posix()
            if rel not in listed:
                missing.append(rel)
    for line in broken:
        print("BROKEN", line)
    for rel in missing:
        print("MISSING", f"{rel}: content page not listed in llms.txt")
    print(
        f"{checked} internal links checked, {len(broken)} broken, "
        f"{len(missing)} pages missing from llms.txt"
    )
    return 1 if (broken or missing) else 0


if __name__ == "__main__":
    sys.exit(main())