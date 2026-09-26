# 0015 — The parser is held to two reference implementations, under one character model

- Status: accepted
- Decided: 2026-09-15

## Where it came from

Porting the builder to JavaScript (0008) needed both implementations to mean the
same thing by whitespace, digits, punctuation and entities. Probing the first
parser for that found content changes its own fidelity check could never see,
because both sides of that check came from the same parser: `๑. ข้อแรก` lost its
`๑.` to a list marker, a non-breaking space at a paragraph's edge disappeared,
`[ab ](u)` lost its space, `&#1;` vanished. A parser can only be trusted against a
reading it did not produce.

## Decision

**Lineage.** The block and inline parsers are a port of commonmark.js 0.31.2
[S24], the CommonMark reference implementation, extended with GFM tables,
strikethrough, task items, extended autolinks and GitHub footnotes. Its licence
travels inside the skill, in `skills/thai-docx/LICENSES/commonmark.js.txt`.

**Two judges, each on its own dialect.** Documents are generated from fixed seeds.
CommonMark-only text is compared with commonmark.js [S24]; GFM text with
cmark-gfm, GitHub's renderer [S25]. Both are reduced to one canonical form —
block structure, text, and each run's formatting — and must match. The build may
refuse a document only where the reference shows raw HTML. `tests/test_oracle.py`
runs a sample on every push; `tests/oracle_campaign.py` runs the large campaigns
recorded in `docs/evidence/`.

**Where the two references disagree, this parser follows commonmark.js and
CommonMark 0.31.2** [S8]. The GFM comparison accepts a mismatch only in one of
these named cases, each checked on a minimal input against both references:

- whitespace a continuation line brings into a code span;
- emphasis beside unpaired strikethrough tildes;
- a code span after an unmatched shorter backtick run;
- a link inside a link around a footnote-style bracket;
- a footnote reference inside image alt text, which cmark-gfm numbers;
- a setext-like underline under a paragraph of link definitions only;
- a paragraph of raw tags only, which HTML shows as nothing.

The GFM corpus also keeps out constructs the core corpus already judges (lazy
lines, trailing tabs, lone tags, empty list items, symbol characters).
cmark-gfm still reads Unicode punctuation as the P categories only; CommonMark
0.31.2 adds S.

**GFM as GitHub renders it.** Where the GFM specification [S9] leaves room,
cmark-gfm decides:

- A task marker counts only on an item's first line, when the item's own marker
  is the first thing on that line; the marker and the spaces after it go.
- A table starts only after CommonMark's block starts have declined the line.
  Once a delimiter row fails its header, that paragraph starts no table. A row
  of nothing but pipes ends a table.
- A footnote reference is tried only once no link matched. `![^x]` is `!` and
  then `[^x]`. An undefined `[^x]` is text.
- Extended autolinks cover `www.`, `http(s)://` and bare email addresses.

  > **Later (2026-09-26):** since 0.2.2 they are found as cmark-gfm's `autolink.c` finds them
  > (a domain read in ASCII, `mailto:` part of its link, an entity at the end left out), save two
  > named cases: `ftp://` and `xmpp:` stay text, the schemes ADR 0040 refuses; and an entity or `*`
  > or `~` inside a bare address, which cmark-gfm reads in the source (references/markdown.md).

**One character model for both implementations.**

- Whitespace is named explicitly: space and tab, and the Zs category where
  CommonMark says Unicode whitespace.
- Punctuation is the Unicode P or S categories, read by code point, never by
  UTF-16 unit.
- List-marker digits are ASCII.
- Link labels are compared after `lower().upper()`.
- Text is NFC.
- Named entities come from one table, `assets/entities.json`, taken from
  CPython's HTML5 table [S26].
- A numeric reference to 0, a surrogate, or anything past U+10FFFF becomes
  U+FFFD. One to a control character, a noncharacter or a line feed stops the
  build, as the same characters typed directly do. A tab is kept.
- Front matter is recognised only as `key: value` lines between `---` fences.
- Rounding is half-up, escaping is spelled out, and every message and flag
  error is fixed text. No `argparse`, whose errors go to stderr.

Left out on purpose:

- Vendoring either reference implementation.
- Following cmark-gfm where it departs from commonmark.js.
- Guaranteeing identical results for characters newer than both Python's
  `unicodedata` and the JavaScript engine's Unicode tables.

## Why

A reference implementation is the one reading of the specification that others
are measured against; holding the parser to it turns "follows CommonMark" from a
claim into a measurement, and a generated corpus finds the corners no hand-written
test thinks of — the campaigns here found and fixed some twenty real defects. Where
two references disagree there is no third to appeal to, so the choice is written
down, tied to a minimal example, and kept narrow enough that an unexplained
difference still fails.

## Expires when

CommonMark or the GFM specification publishes a version this parser does not
follow; GitHub's renderer changes one of the rules above; or the two references
converge on a case listed here, which then stops being a divergence.
