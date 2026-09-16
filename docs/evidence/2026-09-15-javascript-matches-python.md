# 2026-09-15 — the JavaScript file matches the Python package

What this proves: `skills/thai-docx/scripts/thai_docx.js` reads Markdown, writes .docx
bytes, reports on sound and damaged packages, and answers on the command line exactly
as the Python package does (ADR 0008, 0017); it stays within the script limits of ADR
0011; it is the bundle its committed sources build; and each of those claims is held by
a test that goes red when the code behind it is broken (gate
`javascript-matches-python`).

Environment: Linux, Node.js 24.15, Python 3.13, 3.12 and 3.11.16 (python-build-standalone
20260901, checksum verified), pytest 8.4.2, the tree as committed with this record.
Every input is synthetic and seeded.

## 1. The suite

`tests/test_js_parity.py`, 9 tests; the whole suite passes on Python 3.13, 3.12 and 3.11
(156 tests with the step-5 files, 3.11 with `CI=1` and the hash-pinned requirements):

| test | holds |
|---|---|
| `test_bundle_is_built_from_the_committed_sources` | `tools/bundle_js.py --check` and `tools/measure_xml_names.py --check` |
| `test_bundle_stays_within_the_script_limits` | only `fs` and `path`; no child processes, `eval`, `Function`, `fetch`, `import()`, environment, clock or randomness |
| `test_markdown_is_read_the_same` | 4,500 generated texts (CommonMark, GFM, wide Unicode): the same tree, or the same refusal and line |
| `test_build_gives_the_same_result_and_bytes` | 401 builds with images and flag sets: the same JSON and the same .docx bytes |
| `test_check_gives_the_same_report` | 1,508 packages — structural, inflate, XML, fuzzed, damaged — the same report |
| `test_check_decides_each_named_rule_the_same` | 20 hand-made packages, one per reading rule, with the verdict written down — including a one-bit literal/length code and elements nested 20,000 deep |
| `test_deep_nesting_is_read_or_refused_the_same_way` | blockquotes, lists, emphasis and emphasis in a table cell at 98, 100 and 1,000 levels: the same tree or the same refusal and line, and the same build |
| `test_a_writer_defect_is_refused_the_same_way` | the same planted writer defect: exit 1, the same finding, nothing written |
| `test_command_line_is_the_same` | 40 commands, 1,000 nested blockquotes among them, including links, loops, `..`, unreadable and oversized files: the same exit code, stdout, stderr and file; each bounded to 60 s |

## 2. Campaigns on the final code

Seeds never used by the suite. The Markdown campaign ran after the last change to the
parser; the other three after the last change to any source:

| campaign | inputs | differences |
|---|---|---|
| Markdown read (`parity_probe.py 10000 40000`) | 30,000 texts | 0 |
| build (`parity_build.py 3000 60000`) | 3,001 builds, 1,560 written | 0 |
| check (`package_corpus(60000, 30000)`) | 30,008 packages | 0 |
| XML byte fuzz (`xml_fuzz_package`, seed 60000) | 28,000 packages | 0 |

Earlier runs of the same four on seeds 20000 and 40000 also gave 0; the check campaign
produces every finding the checker has, from "entry cannot be read" (about 10,000) to a
single misordered `<w:w>`.

The generators never nest more than a few levels, so depth and size were swept apart,
building each shape with both command lines (60 s bound):

| shape | before | after |
|---|---|---|
| 1,000 nested blockquotes | Python `RecursionError` traceback, Node exit 0 | both exit 2, "blocks nested more than 100 deep", same line |
| 1,000 levels of list in quote; 1,000 nested emphasis | Python traceback, Node exit 0 | both exit 2, same message and line |
| document.xml nested 12,000 deep | Python clean, Node `RangeError` | both clean, to 100,000 deep; malformed after the deep part: both "not well-formed" |
| links, brackets, strikethrough, `<sup>`, footnote chains, 3,000 deep | same | same |
| 60,000 paragraphs; 100,000 emphasis spans | Node past 60 s | same bytes; Node 6.0 s and 15.7 s, Python 7.8 s and 22.7 s |
| 2 MB paragraph; 2,000 columns; 20,000 rows; 5,000 footnotes; 40,000 items | same bytes, Node up to 60 s | same bytes, each under 10 s |

## 3. Planted defects

Each row: one change, the bundle rebuilt, bytecode cleared, the parity suite run (with
`test_check.py` and `test_build.py` for a Python change), every red test read, the tree
restored and its hashes checked. The control run after the last row: 59 passed.

| # | planted defect | file | red |
|---|---|---|---|
| 0 | run without `<w:cs/>` (cause 2) | `js/50-build.js` | writer defect, build, command line |
| 1 | a space for a soft break between Thai characters | `js/40-markdown.js` | Markdown, build, command line |
| 2 | zip date field differs | `js/10-zip.js` | writer defect, build, command line |
| 3 | a duplicate entry name accepted | `js/30-check.js` | check |
| 4 | inflate accepts an incomplete Huffman code | `js/10-zip.js` | named rules |
| 5 | inflate accepts an over-subscribed code | `js/10-zip.js` | named rules |
| 6 | inflate accepts an entry short of its size | `js/10-zip.js` | named rules |
| 7 | a stored entry's two sizes may differ | `js/10-zip.js` | check |
| 8 | the central directory need not add up | `js/10-zip.js` | check |
| 9 | an extra field may run past its entry | `js/10-zip.js` | check |
| 10 | the `xmlns` prefix may be declared | `js/20-xml.js` | named rules |
| 11 | reserved namespaces may be bound | `js/20-xml.js` | named rules |
| 12 | a PI target may run into its data | `js/20-xml.js` | named rules, check |
| 13 | names by fifth-edition ranges, not expat's | `js/20-xml.js` | named rules |
| 14 | `--` accepted in a comment | `js/20-xml.js` | named rules |
| 15 | a file read past the size cap | `js/30-check.js` | command line |
| 16 | `..` applied before a link is followed | `js/90-entry.js` | command line |
| 17 | images read outside the Markdown directory | `js/90-entry.js` | command line |
| 18 | build exits 2, not 1, on a writer defect | `js/90-entry.js` | writer defect |
| 19 | check exits 1, not 2, on an unreadable file | `js/90-entry.js` | command line |
| 20 | JSON escapes non-ASCII | `js/00-base.js` | command line |
| 21 | central directory need not add up | `thai_docx/package.py` | check |
| 22 | inflate keeps what `zipfile` would keep | `thai_docx/package.py` | check |
| 23 | a duplicate entry name accepted | `thai_docx/check.py` | check |
| 24 | `..` applied before a link is followed | `thai_docx/build.py` | command line, `test_build` image directory |
| 25 | links followed without a limit | `thai_docx/build.py` | command line (60 s bound) |
| 26 | no block nesting limit | `thai_docx/markdown.py` | deep nesting, command line |
| 27 | no block nesting limit | `js/40-markdown.js` | deep nesting, command line |
| 28 | no inline nesting limit in paragraphs | `thai_docx/markdown.py` | deep nesting |
| 29 | no inline nesting limit in paragraphs | `js/40-markdown.js` | deep nesting |
| 30 | no inline nesting limit in table cells | `thai_docx/markdown.py` | deep nesting |
| 31 | no inline nesting limit in table cells | `js/40-markdown.js` | deep nesting |
| 32 | first-line indent never reaches the body | `thai_docx/build.py` | build, command line, `test_build` indent |
| 33 | indent reaches quotes, lists and footnotes | `js/50-build.js` | build, command line |
| 34 | indent reaches quotes, lists and footnotes | `thai_docx/build.py` | build, command line, `test_build` indent |
| 35 | an indent may leave no room for text | `js/50-build.js` | build, command line |
| 36 | an indent element written with no indent | `thai_docx/build.py` | goldens, build, command line, nesting, writer defect |
| 37 | committed bundle one byte stale | `thai_docx.js` | bundle built from sources |
| 38 | `require("child_process")` in the sources | `js/90-entry.js` | script limits |

All 39 red (rows 0–31 in one run, control 60 passed; 32–36 after `--indent` was added (ADR 0019), control 62 passed; 37–38 by hand).

## 4. What the first run found

The first run of rows 0–25, against the suite as it stood, left nine green. Each was
read, not explained away:

- **Rows 4, 5, 6, 11, 13, 14.** The campaigns had found and fixed these differences, but
  the suite's seeded corpus reaches them rarely or never: the fixes were held by
  campaigns CI does not run. Each is now a named package with its verdict written down
  (`tests/parity.py::named_packages`) — a dynamic Huffman block with an incomplete and an
  over-subscribed code beside a complete control, an entry whose checksum is taken over
  the zero-padded bytes, each reserved-namespace binding, U+0E2F in a name beside U+0E01,
  `--` and `--->` in comments.
- **Row 18.** Exit 1 from build is reached only by a writer defect, which no input
  produces. The same defect is now planted in both implementations and the results
  compared.
- **Row 25** went red only by a 600-second timeout, and left the command it had started
  looping after the tree was restored. The command-line test now bounds every command to
  60 seconds, and the harness kills its whole process group.
- **Three guards could not be made red by any input**, because a later check always
  refuses the same package with the same verdict: a central-directory record running
  past the directory (rule 5 already requires the records to fill it exactly), a second
  colon in a qualified name, and a colon after a processing-instruction target (every
  caller requires a space, `=`, `/`, `>` or `?>` next). They were removed from both
  implementations where they existed; rows 10 and 12 now plant defects in guards that
  matter. The campaigns in section 2 ran after the removal.
- **An independent review** (a separate agent reading the change, before the first push)
  then built what no generator emits: nesting a thousand deep, and a 12,000-deep XML part.
  Those are the rows 26–31 and the sweeps in section 2.

## 5. Not proved here

- Windows: the path walk's drive and UNC branch (`path.sep === "\\"`) is not exercised
  on Linux.
- Rendering in office applications: ADR 0012's release check, recorded separately.
- Speed. The JavaScript reader's search for the next `&` is held to once per `&`, which is
  what made large parts linear, but no test times it; a regression would show as the
  sweep above, not as a red test.
