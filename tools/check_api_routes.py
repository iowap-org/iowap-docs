#!/usr/bin/env python3
"""Docs drift gate: reference/api.md endpoint tables vs the relay's OpenAPI spec.

Generates the route set in-process from the iowap-server app
(`relay_server.main.app` -> `app.openapi()`), never starts a relay, and diffs
it against the METHOD/Path rows of the endpoint tables in the documentation.

Exit 0 = doc and code agree. Exit 1 = diff report (red PR).

Gate semantics:
- Every route in app.openapi() must be documented (MISSING = fail).
- A Method cell may combine methods via "/" (`GET/POST` maps to one path).
- A Path cell must be exactly one full path — no `/…/` or `·` fold rows
  (UNDOCUMENTED FOLD = fail; folded rows are how drift hides).
- Doc rows that are deliberately outside the schema (include_in_schema=False)
  say so in the Purpose cell via "not in openapi.json" and are skipped;
  without the marker an unmatched row fails (UNKNOWN = fail).

Local use (docs repo checkout next to a iowap-server checkout):
    python3 tools/check_api_routes.py --server ../iowap-server

The iowap-server checkout is inserted at sys.path[0]; the import needs no
`~/.relay/config.yaml` (missing file -> pydantic-settings defaults).
"""

import argparse
import re
import sys
from pathlib import Path

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
METHOD_CELL_RE = re.compile(
    rf"^(?:{'|'.join(HTTP_METHODS)})(?:/(?:{'|'.join(HTTP_METHODS)}))*$"
)
FOLD_RE = re.compile(r"[…·]")
EXEMPT_MARKER = "not in openapi.json"


def openapi_routes(server_dir: Path) -> dict[tuple[str, str], list[str]]:
    """(METHOD, path) -> [operation ids] straight from the FastAPI app."""
    sys.path.insert(0, str(server_dir.resolve()))
    from relay_server.main import app  # noqa: E402  (late import, path added)

    routes: dict[tuple[str, str], list[str]] = {}
    for path, ops in app.openapi()["paths"].items():
        for method, op in ops.items():
            m = method.upper()
            if m in HTTP_METHODS:
                routes.setdefault((m, path), []).append(op.get("operationId", "?"))
    return routes


def doc_rows(doc_path: Path) -> tuple[list[tuple[int, str, str, str, str]], set[tuple[str, str]]]:
    """Parse endpoint rows -> (line_no, METHOD, path, section, purpose-ish tail)."""
    rows: list[tuple[int, str, str, str, str]] = []
    section = ""
    for line_no, line in enumerate(
        doc_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if line.startswith("## "):
            section = line[3:].strip()
        if "|" not in line or line.strip().startswith("|-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not METHOD_CELL_RE.match(cells[0]):
            continue
        method_cell = cells[0].upper()
        path_cell = cells[1]
        tail = " | ".join(cells[2:])
        if not (path_cell.startswith("`") and path_cell.endswith("`")):
            rows.append(
                (line_no, method_cell, f"<UNWRAPPED>{path_cell}", section, tail)
            )
            continue
        path = path_cell[1:-1]
        rows.append((line_no, method_cell, path, section, tail))
    docset = {
        (m, p)
        for _, method_cell, p, _, _ in rows
        for m in method_cell.split("/")
        if not p.startswith("<UNWRAPPED>")
    }
    return rows, docset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--server",
        required=True,
        help="path to an iowap-server checkout (docs CI: ./iowap-server)",
    )
    parser.add_argument(
        "--doc", default="reference/api.md", help="api reference markdown"
    )
    args = parser.parse_args()

    code = openapi_routes(Path(args.server))
    rows, docset = doc_rows(Path(args.doc))

    rc = 0

    missing = sorted(code.keys() - docset)
    if missing:
        rc = 1
        print(f"MISSING IN DOC — registered route not documented ({len(missing)}):")
        for method, path in missing:
            ops = ",".join(code[(method, path)])
            print(f"  {method:7} {path}  ({ops})")

    unknown = docset - code.keys()
    rows_by_path: dict[str, list[tuple[int, str, str]]] = {}
    for line_no, method_cell, path, section, _ in rows:
        if not path.startswith("<UNWRAPPED>"):
            rows_by_path.setdefault(path, []).append((line_no, method_cell, section))
    offending = sorted(
        (m, p, tail)
        for _, method_cell, p, _, tail in rows
        for m in method_cell.split("/")
        if (m, p) in unknown
    )
    offend_fail = [t for t in offending if EXEMPT_MARKER not in t[2]]
    if offend_fail:
        rc = 1
        print(f"UNKNOWN IN DOC — documented row not in app.openapi() ({len(offend_fail)}):")
        printed: set[str] = set()
        for _m, path, _tail in offend_fail:
            if path in printed:
                continue
            printed.add(path)
            for line_no, method_cell, section in rows_by_path.get(path, []):
                print(f"  api.md:{line_no}  [{section}]  {method_cell} {path}")
    exempt = {(m, p) for (m, p, tail) in offending if EXEMPT_MARKER in tail}
    if exempt:
        print(f"SKIPPED (marked '{EXEMPT_MARKER}'): {len(exempt)} doc rows.")

    bad_rows: list[str] = []
    dup_keys: set[tuple[str, str]] = set()
    seen: set[tuple[str, str]] = set()
    for line_no, method_cell, path, section, _ in rows:
        if path.startswith("<UNWRAPPED>"):
            bad_rows.append(
                f"  api.md:{line_no}  [{section}]  path cell lacks backticks: {path[len('<UNWRAPPED>'):]}"
            )
            dup_keys.add((method_cell, path))
            continue
        if FOLD_RE.search(path):
            bad_rows.append(
                f"  api.md:{line_no}  [{section}]  fold row ({method_cell} {path}) — expand to the full path"
            )
        for m in method_cell.split("/") if not path.startswith("<UNWRAPPED>") else []:
            key = (m, path)
            if key in seen:
                dup_keys.add(key)
            seen.add(key)
    if bad_rows:
        rc = 1
        print(f"BROKEN / FOLD ROWS ({len(bad_rows)}):")
        for msg in sorted(bad_rows):
            print(msg)
    if dup_keys:
        rc = 1
        print(f"DUPLICATE ROWS ({len(dup_keys)}):")
        for line_no, method_cell, path, section, _ in rows:
            for m in method_cell.split("/") if not path.startswith("<UNWRAPPED>") else []:
                if (m, path) in dup_keys:
                    print(f"  api.md:{line_no}  [{section}]  {m} {path}")
                    break

    if rc:
        print(
            f"\nDrift detected: {len(code)} code routes vs {len(docset)} doc rows "
            f"({len(missing)} missing / {len(offending)} unknown)."
        )
        return rc

    print(
        f"OK: {len(docset)} documented endpoint rows cover "
        f"{len(code)} code routes ({len(exempt)} marked outside the schema)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())