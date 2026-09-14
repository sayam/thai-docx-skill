# 2026-09-15 — the build: goldens, fidelity, and 20 planted defects

What this proves: `thai_docx build` gives the same bytes on every run (ADR 0008),
refuses to write a package that fails its own checker or differs from the
Markdown (ADR 0005, 0007), and each of those guarantees is held by a test that
fails when the code behind it is broken (practice *a mutation is watched, not
assumed*; gate `checkers-proven-two-way`).

Environment: Python 3.13 on Linux, pytest 8.4.2, the tree as committed after
`510c3a1`. `tests/fixtures/sample.md` is synthetic text covering every construct
ADR 0010 accepts; `pixel.png` is a generated 200×50 image.

## 1. Goldens

Built twice by the CLI, compared with `cmp`: identical. Committed under
`tests/golden/` and held by `test_sample_matches_golden_bytes`.

| file | flags | sha256 |
|---|---|---|
| `sample-default.docx` | none | `122e25533920449c658b67677bf4b92beabec836d247ffe33fc4e54aeb669c36` |
| `sample-all-flags.docx` | `--toc --page-numbers --hide-spelling-errors --align thai --paper letter --size 15 --margins 1,1,1,1` | `8d43897feb06ac5175d712dfdac5f6acc2ae7d672a85a6a38547e3424fb8e207` |

Both pass `thai_docx check` with no findings and no warnings. Zip entries are
stored (not deflated) with the timestamp 1980-01-01 and no OS attributes, so
the JavaScript port of ADR 0008 has fixed bytes to match.

`test_sample_text_round_trips_paragraph_for_paragraph` compares the text read
back from the golden with the text the Markdown renders: 45 paragraphs, equal.

## 2. Mutation run

Each row: one line of `build.py` or `markdown.py` changed, `pytest -q -x tests`
run, tree restored and re-run green (92 passed).

| planted defect | suite |
|---|---|
| bold without `bCs` (cause 5) | red |
| `w:lang` without `bidi` (cause 2) | red |
| compatibility mode 14 (cause 1) | red |
| text not XML-escaped | red |
| fidelity check disabled | red |
| file written despite findings | red |
| task mark `[ ]` instead of ☐ | red (fidelity) |
| zip entries deflated | red (golden) |
| zip timestamp from the clock | red (golden) |
| image directory limit removed (ADR 0011 §4) | red |
| remote image accepted | red |
| unreferenced footnote kept quiet | red |
| hyperlink target not attribute-escaped | red |
| adjacent same-format runs not merged (cause 4) | red |
| Thai soft break gets a space (ADR 0005 §1) | red |
| extra table cells dropped | red |
| `<span>` allowed | red |
| invisible character in input accepted | red |
| intraword underscore emphasised | **green** → test added (`foo_bar_` stays literal), then red |
| hard break lost | red |

Two rows were first reported green because the harness had not applied the
mutation (a `\n` in the pattern was literal); re-run with the mutation applied,
both are red. The one true green named a missing test, which is now in
`test_intraword_underscore_is_literal_but_star_is_not`.

## 3. Not proved here

Rendering. No office application is installed on this machine; whether Word,
LibreOffice, Google Docs and WPS show these files as ADR 0012 requires is the
maintainer's release check, recorded separately when it is done.
