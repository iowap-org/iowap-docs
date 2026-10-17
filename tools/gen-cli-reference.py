#!/usr/bin/env python3
"""Generate reference/cli.md from the live node-cli argparse tree.

The parser is the contract: every command/subcommand/flag/help line lands
in the table, so the page can't drift from the code. Re-run whenever
commands change (script lives in .hermes/cache/scratch — promoted there by
the docs task; regenerate = `python3 gen-cli-reference.py`).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, os.environ.get("IOWAP_NODE_REPO", str(Path.home() / "projects/iowap-node")))
import os  # noqa: E402

from nodes.common import node_cli  # noqa: E402

SKIP_GLOBAL = {"json", "log_level", "func", "help"}


def clean_help(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.split()).replace("|", "\\|")


def is_flag(action) -> bool:
    return bool(getattr(action, "option_strings", None))


def flag_label(action) -> str:
    flags = ", ".join(action.option_strings)
    if action.metavar:
        mv = str(action.metavar)
        mv = mv if mv.startswith("<") else f"<{mv}>"
        return f"{flags} {mv}"
    return flags


def arg_label(action) -> str:
    return f"`{action.metavar or action.dest}`"


def rows_for(parser) -> list[tuple[str, str]]:
    """(label, help) for non-global, non-help actions; positional first."""
    pos, opt = [], []
    for action in parser._actions:
        if getattr(action, "dest", "") in SKIP_GLOBAL:
            continue
        if action.dest == "help":
            continue
        if isinstance(action, argparse._SubParsersAction):
            continue
        if is_flag(action):
            opt.append((flag_label(action), clean_help(action.help)))
        else:
            pos.append((arg_label(action), clean_help(action.help) + " *(positional)*"))
    return pos + opt


def subparsers_of(parser) -> dict[str, tuple[argparse.ArgumentParser, str]]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            help_map = {
                getattr(c, "dest", None) or getattr(c, "metavar", None): c.help
                for c in action._choices_actions
            }
            return {name: (sub, help_map.get(name, ""))
                    for name, sub in action.choices.items()}
    return {}


def emit(parser, title: str, purpose: str, level: int, out: list[str]) -> None:
    heading = "#" * (level + 2)
    if title:
        out.append(f"{heading} `{title}`\n")
        if purpose and purpose != title:
            out.append(f"{purpose}\n")
    rows = rows_for(parser)
    if rows:
        out.append("| Argument/Flag | Meaning |")
        out.append("|---|---|")
        out.extend([f"| `{lbl}` | {h} |" for lbl, h in rows])
        out.append("")
    elif title and not subparsers_of(parser):
        out.append("*(no additional arguments — global flags apply)*\n")
    for name, (sub, sub_help) in subparsers_of(parser).items():
        emit(sub, f"{title} {name}".strip(), clean_help(sub_help), level + 1, out)


parts: list[str] = [
    "## CLI Reference (node-cli)",
    "",
    "Every command, subcommand, flag and its help of the **node** CLI — "
    "generated **from the live argparse tree** (the parser is the contract): "
    "this page matches the executable that ships from the same tree. "
    "Narrative flows live in [node/cli](../node/cli.md); the relay's HTTP "
    "surface in [api](api.md).",
    "",
    "### Global flags\n",
    "| Flag | Meaning |",
    "|---|---|",
    "| `--json` | machine-readable single-line JSON for every command |",
    "| `--log-level` | verbosity of the human output |",
    "",
]
top = node_cli.build_parser()
groups = subparsers_of(top)
parts.append("### Commands\n")
parts.append("| Command | Purpose |")
parts.append("|---|---|")
for name, (_sub, sub_help) in groups.items():
    parts.append(f"| `{name}` | {clean_help(sub_help)} |")
parts.append("")
for name, (sub, sub_help) in groups.items():
    emit(sub, name, clean_help(sub_help), 1, parts)
text = "\n".join(parts)
for junk in ("```",):
    pass
out_path = Path("/home/felix/projects/iowap-docs/reference/cli.md")
out_path.write_text(text)
print("written:", out_path, len(text), "chars |", len(groups), "commands:",
      ", ".join(groups))