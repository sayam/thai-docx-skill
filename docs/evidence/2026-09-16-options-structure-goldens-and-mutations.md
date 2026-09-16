# 2026-09-16 — the options, heading styles and thesis structure: goldens and 23 planted defects

What this proves: the build options added after 2026-09-15 (paper and page, numbers,
headers and footers, tables, line spacing), heading styles from the front matter (ADR 0020),
and regions, sections, captions and lists (ADR 0021) are each held by a test that fails when
the code behind them is broken; the goldens are the files the release is opened in (gate
`release-oracle-set-is-the-goldens`); and Python and JavaScript still give the same bytes
(gate `javascript-matches-python`).

Environment: Linux, Python 3.13.3, pytest 8.4.2, Node.js 24.15; the working tree of this
record, not yet committed. Content synthetic (ADR 0011 §8): `tests/fixtures/thesis/` is a
written-for-the-purpose thesis with two generated PNG images.

## 1. Goldens

The two goldens of 2026-09-15 were built again on purpose, twice, each change read in the
parts before it was accepted:

- table cells gained `w:tblCellMar` (108 twips left and right) and no space after their
  paragraphs, after Word showed text against the borders — `word/document.xml` only;
- `--toc` and `--page-numbers` now write the TOC 1–3 and Header styles, after Word showed
  a table of contents and page number in Angsana New 20 pt from its own template —
  `word/styles.xml` and `word/header1.xml` only.

Three goldens were added from the thesis fixture, one per variant of `tools/oracle_set.py`.

| golden | source | flags | sha256 |
|---|---|---|---|
| `sample-default.docx` | `sample.md` | none | `77d0de9a531de3a032b70b71946a86da280e617977e1d54af97c61d9931a34ed` |
| `sample-all-flags.docx` | `sample.md` | `--toc --page-numbers --hide-spelling-errors --align thai --paper letter --size 15 --margins 1,1,1,1` | `a162c919b5e060d8db6e4a44acca672e419527a70392eecd55f9721709fb9f2f` |
| `thesis-text.docx` | `thesis/thesis.md` | `oracle_set.VARIANTS["sample-text"]` | `aac5b2c368dd1efc03fda060bb02895a3c61d090f4aab5bac8772a723012d0bd` |
| `thesis-options.docx` | `thesis/thesis.md` | `oracle_set.VARIANTS["sample-options"]` | `a83471fd0b02a3e5eda4c3cc7a54079f3f0f51e0ce876fbe7294d57d8c53fc4d` |
| `thesis-layout.docx` | `thesis/thesis.md` | `oracle_set.VARIANTS["sample-layout"]` | `9d97b9b1edd8a730414740f509eecd8caf8e2195db975d42e11673429da01fe0` |

All five pass `thai_docx check` with no findings and no warnings. The Python and JavaScript
command lines build the three thesis goldens byte for byte (`test_command_line_is_the_same`),
and `tools/oracle_set.py` writes each variant for five applications with the golden's bytes
(`test_every_variant_for_every_application_is_its_golden`). Suite: 180 passed.

## 2. Mutation run

Each row: one change, the named test file run, every red test read, the file restored and
its sha256 checked; a JavaScript change was bundled before the run and after the restore,
and `bundle_js.py --check` passed at the end. Run twice: first with `-x` (the first red),
then with the goldens and the oracle set deselected, to see that a test of its own holds
each defect and not the goldens alone.

| planted defect | first red (`-x`) | red without the goldens |
|---|---|---|
| caption number drops the chapter | golden thesis-text | regions test |
| heading outside the chapters keeps its number | golden thesis-text | regions; appendices |
| appendix list linked to the Heading styles | golden thesis-text | appendices |
| front pages ignore `--front-page-numbers` | golden thesis-options | appendices |
| section closed in an empty paragraph of its own | golden thesis-text | regions |
| region order not checked | appendices | appendices; region refusals |
| SEQ count not restarted at a `#` | golden thesis-text | regions; appendices |
| caption keeps its `Table:` prefix | golden thesis-text | regions; appendices; no-region captions |
| misspelt region comment kept quiet | warnings test | warnings test |
| `Figure:` inside the image paragraph kept quiet | warnings test | warnings test |
| heading colour not written | golden thesis-text | heading styles |
| unknown heading property accepted | heading-style refusals | heading-style refusals |
| line spacing fixed at 1.1 | golden thesis-options | line spacing |
| bottom-center number put in the header | golden thesis-text | page numbers; regions; header/footer; first page; applied styles |
| `--thai-digits` leaves list numbers Arabic | golden thesis-options | heading numbers; Thai digits |
| `--table-widths auto` gives equal columns | golden thesis-options | table widths |
| table cells lose their margins | golden sample-default | table header row |
| TOC styles not written | golden sample-all-flags | applied styles |
| header text not escaped | header/footer | header/footer |
| landscape keeps the portrait width | golden thesis-layout | landscape |
| `--no-page-number-first` accepted without `--page-numbers` | first page | first page |
| oracle set variant flags drift from the golden | oracle set | — (only the oracle set holds it) |
| JavaScript caption count off by one | build parity | build parity; command line |

All 23 red. The last-but-one row has no second column by design: the variants are what that
gate holds.

## 3. Not proved here

- Rendering: that Word, LibreOffice, Google Docs and WPS show these files as ADR 0012 and the
  checklist ask — the maintainer's release check, with `tools/oracle_set.py`.
- Whether Word's `thaiLetters` numbers skip ฃ and ฅ as the build's caption numbers do.
- Python 3.11: this machine no longer has the 3.11 build used on 2026-09-15; CI runs it.
