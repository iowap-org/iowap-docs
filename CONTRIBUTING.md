# Contributing to IOWAP Documentation

This repo holds the user-facing documentation for the IOWAP ecosystem.
It is served live by every relay at `/relay/v2/docs/`. The page-contract
below keeps every page human-readable **and** machine-predictable.

## The page contract

**Titles bind to the glossary.** Use exactly the terms defined in
[concepts/glossary.md](concepts/glossary.md) — one vocabulary for humans
and machines, no synonyms.

**Reserved section skeletons** (stable anchors for readers and AI
consumers):

| Page type | Section skeleton | Target length |
|-----------|------------------|---------------|
| Concept | `What it is` → `How it works` → `What it is NOT` → `Related pages` | ~≤ 100 lines |
| Ops / Tutorial | numbered `## N. Step` + `## Verification` + `## Troubleshooting` | as needed |
| Reference | tables over prose, language-tagged code | as needed |

Additional sections are allowed; the reserved ones keep their names and
order.

**Commands:** one command per fenced code block with a language tag, the
expected output as `# -> ` comment inside or right after the block.
Values come from real captures, never invented.

**Status quo only:** no task ids (`T-xxx`), no phase numbers, no dates in
prose. Version hints only where functionally relevant (`since 2.3.9`).
History lives in git and the project boards.

**Not-implemented features** live only in `federation/` or in clearly
marked `> **⚠️ Not implemented**` boxes — never mixed into operational
text.

**One topic, one page:** model facts live in exactly one `concepts/`
page; ops pages link instead of repeating.

## Renderer limits

Pages render through python-markdown with `fenced_code` + `tables` only.
Use: headings, tables, fenced code, plain blockquotes. **Do not use:**
admonitions (`!!! note`), GitHub alerts (`> [!WARNING]`), task lists
(`- [x]`), raw HTML, intra-page anchor links, YAML frontmatter.

## House rules

- English only.
- IPs and hostnames in examples: RFC 5737 test ranges (`192.0.2.x`,
  `203.0.113.x`) and `example.com` — never real addresses.
- Relative links (check_links.py enforces them).
- Max folder depth 3; slugs derive from paths — renaming a path breaks
  bookmarks, so do not rename casually (no new aliases are added; slug
  stability is a compatibility contract).

## Adding a page

1. Write it to the right tree position (see README structure map).
2. Follow the page contract; run the jargon self-check:
   `grep -nE '^#{1,3} .*\((T-[0-9]+|Phase [0-9]+)\)' <file>` → must be empty.
3. Add it to `llms.txt` (one line, correct section) **and** link it from
   at least one other page (no orphans).
4. `python3 tools/check_links.py` → 0 broken.

## CI

`tools/check_links.py` runs on every push/PR (`.github/workflows/`) —
no broken internal links, no orphans from llms.txt.