# 2026-09-17 — every source file names its copyright and licence

What this proves: the project's source files — the skill's Python and JavaScript, the tests and
the project's own tools — open with SPDX lines a tool can read, the two commonmark.js ports name
their upstream author and BSD-2-Clause, the bundle states its parts' lines once, and
`tests/test_licensing.py` turns red when any of that is missing.

Environment: Linux, Python 3.13, Node.js 24. Base: `main` with the governance pages.

## What the files carry

- One or more `SPDX-FileCopyrightText: <year> <holder>` lines, then `SPDX-License-Identifier: MIT`.
  Any holder is accepted: a contributor keeps the copyright of what they write (maintainer,
  2026-09-17).
- `skills/thai-docx/scripts/thai_docx/markdown.py` and `js/40-markdown.js` also carry
  `2014 John MacFarlane` and `MIT AND BSD-2-Clause`, as `skills/thai-docx/LICENSES/commonmark.js.txt`
  says.
- `tools/bundle_js.py` takes each part's lines off and writes them once after the shebang; the
  bundle's body is unchanged.
- The verifiable-gates files in `tools/` keep their own headers (Apache-2.0).

## Nothing else changed

Suite 222 passed; `bundle_js.py --check` current; ruff, ESLint and the doctor pass; coverage 98%.

## Planted defects

| planted | result |
|---|---|
| a new test file without the lines (`tests/test_script_limits.py`, as it came from its pull request) | red: `these files do not open with their SPDX lines: {'tests/test_script_limits.py': []}` |
| both lines deleted from `thai_docx/check.py` | red, naming `check.py` |
| `js/40-markdown.js` reduced to plain MIT, the upstream author dropped | red, naming `js/40-markdown.js` with the two lines it has |

Each was restored; the suite is green again.
