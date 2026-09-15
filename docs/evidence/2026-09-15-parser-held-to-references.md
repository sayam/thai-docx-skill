# 2026-09-15 — the parser held to commonmark.js and cmark-gfm

What this proves: the Markdown parser reads generated documents as the CommonMark
reference implementation does (CommonMark-only text) and as GitHub's renderer does
(GFM text), outside the divergences ADR 0015 names; the build refuses only what the
reference shows as raw HTML; and each rule decided on the way is held by a test
that fails when the rule is broken.

Environment: Python 3.13 on Linux, Node.js 24, commonmark.js 0.31.2 (npm, locked
in `tests/js/package-lock.json`), cmarkgfm 2025.10.22, the tree as committed with
this record. Every document is synthetic, generated from its seed.

## 1. Why the parser was replaced

Before porting to JavaScript, the first parser was probed for Python-only
behaviour. It changed content in ways its own fidelity check could not see, since
both sides of that check came from it:

| input | first parser | CommonMark |
|---|---|---|
| `๑. ข้อแรก` | a list item; `๑.` gone | a paragraph, `๑.` kept |
| NBSP at a paragraph's edge | removed | kept |
| `[ab ](u)` | link text `ab` | `ab ` |
| `&#1;` | removed | U+FFFD (this skill: refused, ADR 0015) |

It was replaced by a port of commonmark.js 0.31.2. Porting from memory first, then
from the package's source, is itself recorded: four places written from memory did
not match the real code and were found by the comparison below, not by reading.

## 2. Campaigns on the final code

`python3 tests/oracle_campaign.py core 100000 50000`

```
{"corpus": "core", "reference": "commonmark.js 0.31.2", "seeds": [100000, 150000],
 "refused": {"HTML blocks are not supported": 984, "an HTML comment block also holds text": 1500,
             "HTML <b> is not supported": 3, "HTML <word> is not supported": 3, "HTML <a> is not supported": 1,
             "HTML declarations, processing instructions and CDATA are not": 1},
 "unjustified_refusals": [], "unexplained": []}
```

`python3 tests/oracle_campaign.py gfm 100000 50000`

```
{"corpus": "gfm", "reference": "cmark-gfm (cmarkgfm 2025.10.22)", "seeds": [100000, 150000],
 "refused": {"table row has 3 cells": 40, "table row has 2 cells": 36, "footnote [^1] is defined twice": 8,
             "HTML <a> is not supported": 8, "HTML <b> is not supported": 6, "HTML <foo> is not supported": 6,
             "footnote [^1] is defined but never referenced": 6, "HTML declarations, processing instructions and CDATA are not": 5,
             "footnote [^n] is defined but never referenced": 4, "HTML <bar> is not supported": 2,
             "HTML <word> is not supported": 1, "HTML <ab> is not supported": 1, "HTML blocks are not supported": 1},
 "known_divergences": {"emphasis beside unpaired strikethrough tildes": 17,
                       "paragraph of raw tags only, which HTML shows as nothing": 2,
                       "code span after an unmatched shorter backtick run (cmark-gfm misses it)": 2,
                       "link inside a link around a footnote-style bracket (cmark-gfm; commonmark.js refuses it)": 1},
 "unexplained": []}
```

Before these, the development campaigns covered about 83,000 core and 60,000 GFM
documents on earlier seeds; every unexplained mismatch they found was either fixed
in the parser, fixed in the comparison, or reduced to a minimal input and checked
against both references before it became a named case in ADR 0015.

## 3. Defects the campaigns found in the parser

Fixed, each now held by a unit test or by the oracle test:

- Footnote-looking text: `[^_^]` stopped the build (now text, as GitHub).
- A task item's marker was read in blockquotes and after another list marker.
  Trailing spaces after it were mishandled. A task item heading a table or a
  setext heading lost its checkbox.
- Tables:
  - started before CommonMark's own block starts;
  - required a pipe in the delimiter row;
  - continued through a row of pipes;
  - started again after a failed delimiter row.
- A comment block alone in a list item emptied the item.
- A comment before a line break let the trailing spaces be stripped.
- A document opening with `---` lost the text up to the next `---` as front
  matter.
- Footnote references were tried before links. `![^x]` made an image.
- Bare email and `http(s)://` autolink rules did not follow GitHub's.
- Indented code finalization, link reference definitions removed per paragraph
  instead of per document, case-insensitive inline HTML, and `parseReference`'s
  title handling all differed from commonmark.js.
- Soft break next to an entity, at a paragraph's edge, or next to another soft
  break.
- `&#10;` passed through.

## 4. Mutation run

Each row: one line of `markdown.py` changed, `pytest -q -x tests` run, tree restored.

| planted defect | suite |
|---|---|
| punctuation is P only, not P or S | red |
| rule of three ignored | red |
| intraword underscore opens emphasis | red |
| lazy continuation disabled | red |
| list padding: five spaces not special | red |
| any ordered list may interrupt a paragraph | red |
| partially consumed tab not expanded | red |
| comment node dropped | red |
| link definitions not removed at document end | red |
| table start before setext | red |
| failed delimiter row forgotten | red |
| pipe-only row continues a table | red |
| task marker after `>` or a list marker | red |
| footnote tried before links | red |
| email autolinks off | red |
| Thai soft break gets a space | red |
| trailing soft break keeps a space | red |
| control character reference accepted | red |
| front matter takes any lines | **green** → test added, then red |
| NBSP stripped at a paragraph's edge | red |
| list-marker digits read as Unicode `\d` | green — *equivalent*: `re_maybe_special` admits only ASCII digits to the block starts, so no input reaches the marker regex with another digit |

Final state: 131 passed; both goldens unchanged and clean under `thai_docx check`.
