# 2026-09-18 — the first CodeQL alerts on main: two fixed, one dismissed with its reason

What this proves: every alert CodeQL's security-extended queries raised on `main` after the
workflow was added (12, all of security severity "high") was either fixed in the code or dismissed
with a written reason, as CONTRIBUTING.md ("Static analysis") requires; and the one alert that
pointed at a real weakness turned out to be one: `profile show /dev/zero` never finished.

Environment: Linux, Python 3.13, Node.js 24; CodeQL `security-extended` from
`.github/workflows/codeql.yml` (codeql-action v4.38.0), run on `main` at 05efd55 and later.

## The alerts

| alert | rule | where | what was done |
|---|---|---|---|
| 9, 10 | `js/file-system-race` | `js/55-profiles.js` `profileRead`, and the bundle | **fixed** |
| 7, 8 | `js/incomplete-sanitization` | `tests/js/eslint.config.cjs`, lines 39 and 51 | **fixed** |
| 1–6, 11, 12 | `js/bad-tag-filter`, `py/bad-tag-filter` | the Markdown parsers: `reHtmlBlockClose` / `re_html_block_close` and `RE_DIRECTIVE` / `re_directive`, in `js/40-markdown.js`, `markdown.py` and the bundle | **dismissed: false positive** |

### `file-system-race` — fixed

Both implementations asked a profile's size, then read the whole file. Between the two the file
can change; and a file with no size is not a regular file, so the check was skipped and the read
never ended. Before the fix, `thai_docx profile show /dev/zero` ran until killed (20 s timeout),
in Python and in JavaScript alike.

Now both open the file and read at most 64 KiB + 1 bytes; one byte more than the limit is refused
as "larger than 64 KiB". The messages are unchanged. `/dev/zero` is refused at once, and a case for
it is in `tests/test_profiles.py` and in the command-line parity cases of `tests/test_js_parity.py`.
The Python side had the same pattern; CodeQL's Python queries did not flag it, and it is fixed the
same way so the two stay one behaviour.

### `incomplete-sanitization` — fixed

The ESLint config built regular expressions from the names each JavaScript part declares, escaping
only `$`. The names are JavaScript identifiers, so nothing else could occur, but the escaping is now
complete (`escapeRegExp`). ESLint still passes, and a planted unused function is still reported.

### `bad-tag-filter` — dismissed as false positive

The rule is about regular expressions used to find or strip HTML for safety, where a pattern that
misses `--!>` or a newline lets markup through to a browser. These are not such filters:

- `-->` in `reHtmlBlockClose[2]` is the end condition of an HTML block of type 2 as the CommonMark
  specification (0.31.2, section 4.6) defines it, ported from commonmark.js; the parser is held to
  commonmark.js and cmark-gfm by the generated-input campaigns (docs/evidence/2026-09-15-parser-held-to-references.md).
  A different end condition would read documents differently from every CommonMark implementation.
- `RE_DIRECTIVE` / `re_directive` recognises a one-line layout directive such as `<!-- toc -->`
  (ADR 0021); a comment that does not match is simply not a directive.
- Nothing the skill writes is HTML. An HTML comment renders nothing in the Word file, and every
  other HTML block is refused (references/markdown.md). There is no browser on the output side for
  unfiltered markup to reach.

Each alert was dismissed with the reason "false positive" and a comment pointing here.

## Checks

- Suite 222 passed; coverage 98% (floor 97); `bundle_js.py --check` current; ruff, ESLint and the
  doctor pass.
