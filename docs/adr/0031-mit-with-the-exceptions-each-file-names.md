# 0031 — MIT, with every exception named in the file that carries it (restated)

- Status: accepted
- Decided: 2026-09-18
- Supersedes: 0003

## Where it came from

0003 said "the whole repository is MIT-licensed", which was true when the repository held only
its own code. It no longer is: `tools/` carries the verifiable-gates files under Apache-2.0 and
their rule texts under CC BY 4.0, and two files port commonmark.js, which is BSD-2-Clause. Since
2026-09-18 every source file opens with SPDX lines, so the licence of a file is readable from the
file rather than from a sentence about the repository.

## Decision

- **The project's own work is MIT**, and `LICENSE` at the root is the notice for it.
- **Every source file names its own copyright and licence** in SPDX lines at the top:
  `SPDX-FileCopyrightText: <year> <holder>` (one line per holder; a contributor keeps the
  copyright of what they write) and `SPDX-License-Identifier`. The gate
  `sources-name-their-licence` holds it.
- **The exceptions, each named where it lives:**
  - `skills/thai-docx/scripts/thai_docx/markdown.py` and `js/40-markdown.js` port commonmark.js:
    `MIT AND BSD-2-Clause`, with John MacFarlane as a copyright holder, and the upstream text at
    `skills/thai-docx/LICENSES/commonmark.js.txt`;
  - the verifiable-gates files under `tools/`: Apache-2.0, and the rule texts in
    `tools/overlay.json` CC BY 4.0, as `tools/LICENSE` says. They are not shipped with the skill.
- **The skill directory carries the notice it needs on its own**: `skills/thai-docx/LICENSE.txt`,
  `LICENSES/` for the port, and `license: MIT` in the front matter — the archive of ADR 0018
  carries all three.
- The README states the exceptions in one paragraph, for a reader who does not open files.

Left out on purpose: the REUSE layout (`LICENSES/MIT.txt` at the root, every file registered).
The per-file tags answer the question REUSE asks; the layout can follow if a tool needs it.

## Why

A single sentence about a repository stops being true the moment one file arrives from somewhere
else, and a reader has no way to notice. A tag in the file travels with the file — into the
release archive, into a fork, into a copy someone pastes — and a test can check that every file
has one, which no sentence can.

## Expires when

The project takes code under a licence MIT cannot sit beside, a contributor needs an explicit
patent grant, or a tool requires the REUSE layout.
