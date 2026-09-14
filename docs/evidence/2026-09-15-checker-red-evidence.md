# 2026-09-15 — the checker goes red on legacy generators, and on 16 planted defects

What this proves: `thai_docx check` reports the causes of ADR 0004 on files that
generators without this skill produce (gate `gates-carry-red-evidence`), and each
of its checks is held by a test that fails when that check is broken (practice
*a mutation is watched, not assumed*).

Environment: Python 3.13 on Linux, pytest 8.4.2, the checker as first committed
after `4d91e9b`. Fixtures are synthetic text; nothing from a real document.

## 1. Legacy fixtures

Both under `tests/fixtures/`, generated with python-docx 1.2.0 from three short
synthetic Thai paragraphs.

### `legacy-python-docx-default.docx` — python-docx used with no skill

`python3 skills/thai-docx/scripts/thai_docx check tests/fixtures/legacy-python-docx-default.docx` · exit 1

```
{"ok": false, "counts": {"runs": 4, "paragraphs": 3, "tables": 0}}
1         word/settings.xml      compatibilityMode declared as ['14']; must be exactly one 15
2         word/document.xml      a run with text has no <w:cs/> element
2         word/document.xml      a run with text has no <w:cs/> element
5         word/document.xml      in a run, <w:b> has no <w:bCs> beside it
2         word/document.xml      a run with text has no <w:cs/> element
2         word/document.xml      a run with text has no <w:cs/> element
5         word/styles.xml        in a style, w:rFonts names a Latin font but no w:cs font
5         word/styles.xml        in a style, w:rFonts names a Latin font but no w:cs font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
```

Causes 1 (compatibility mode 14), 2 (no run marked complex script) and 5 (Latin
fonts without a complex-script font in styles; Symbol bullets). Causes 3 and 4
are absent because python-docx neither switches proofing off nor splits runs.

### `legacy-helper-2026-09-14.docx` — the helper from the handoff [S2], used as documented

`python3 skills/thai-docx/scripts/thai_docx check tests/fixtures/legacy-helper-2026-09-14.docx` · exit 1

```
{"ok": false, "counts": {"runs": 3, "paragraphs": 2, "tables": 0}}
order     word/settings.xml      in w:settings, <w:hideSpellingErrors> must come before <w:hideGrammaticalErrors>
1         word/settings.xml      compatibilityMode declared as ['14', '15']; must be exactly one 15
order     word/document.xml      in a run's w:rPr, <w:szCs> must come before <w:lang>
5         word/document.xml      in a run, <w:b> has no <w:bCs> beside it
5         word/document.xml      in a run, <w:i> has no <w:iCs> beside it
order     word/document.xml      in a run's w:rPr, <w:szCs> must come before <w:lang>
5         word/document.xml      in a run, <w:b> has no <w:bCs> beside it
5         word/document.xml      in a run, <w:i> has no <w:iCs> beside it
order     word/document.xml      in a run's w:rPr, <w:szCs> must come before <w:lang>
5         word/document.xml      in a run, <w:b> has no <w:bCs> beside it
5         word/document.xml      in a run, <w:i> has no <w:iCs> beside it
order     word/styles.xml        in a style's w:rPr, <w:szCs> must come before <w:lang>
5         word/styles.xml        in a style, w:rFonts names a Latin font but no w:cs font
5         word/styles.xml        in a style, w:rFonts names a Latin font but no w:cs font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
5         word/numbering.xml     a bullet level uses the Symbol font; bullets need a Thai-capable font
```

The helper set `<w:cs/>` and `w:bidi` on every run (cause 2 is gone) but
declared compatibility mode a second time instead of replacing the template's
14, placed `szCs` after `lang` and the hide-errors settings out of order — each
a property Word may ignore without error — and left `bCs`/`iCs` and the Symbol
bullets untouched. This is the file the handoff's own diagnosis was written
against, so it is the red the checker had to produce.

## 2. Mutation run

Each row: one line of `check.py` changed, `pytest -q tests` run, tree restored
and re-run green. The table is what the run printed.

| planted defect | suite |
|---|---|
| cause 1 never reported | 5 failed |
| cause 2: `<w:cs/>` never required | 4 failed |
| cause 2: any `w:bidi` accepted | 1 failed |
| cause 3 never reported | 1 failed |
| cause 4 never reported | 1 failed |
| cause 4: rsid attributes no longer ignored | **31 passed — green** → test added, then 1 failed |
| cause 5: Latin font without cs font | 1 failed |
| cause 5: twins (`szCs`/`bCs`/`iCs`) | 3 failed |
| cause 5: Symbol bullet | 1 failed |
| order never reported | 4 failed |
| invisible character never reported | 5 failed |
| DOCTYPE not refused | 5 failed |
| size cap ignored | 1 failed |
| font warning silent | 1 failed |
| footnotes part skipped | 1 failed |
| exit code always 0 | 1 failed |

The one green mutation named a missing test
(`test_cause_4_rsid_attributes_do_not_hide_a_split`); with it in place the same
mutation fails. Final state: 32 passed, working tree equal to the committed
checker.
