# 2026-09-17 — Word for macOS: the fifth application, and a line spread letter by letter

What this proves: the release documents of `tools/oracle_set.py` were opened in Microsoft Word
for macOS, the one application of ADR 0012 left unchecked on 2026-09-16
(`2026-09-16-office-check-five-applications.md`); what it showed was read against the
checklist; one fault in the package was found there and fixed, and the fix is held by a named
test as well as the goldens (gates `release-oracle-set-is-the-goldens`,
`build-faithful-and-byte-stable`).

Environment: Microsoft Word for macOS, Thai proofing language; the files of `main` at
06ce4ef (`sample-text-word_mac.docx`, `sample-options-word_mac.docx`), opened by the
maintainer with formatting marks shown. Content synthetic (`tests/fixtures/thesis/`).

## 1. What was right

Read against the checklist, from the maintainer's screenshots:

- **sample-text:** status bar "Thai"; no squiggles under correctly spelled Thai; Thai lines
  break inside words; the abstract heading centred and bold; 23 pages.
- **sample-options:** the header text on every page; the cover paragraphs with their 0.5 in
  first-line indent and 1.5 line spacing; body paragraphs Thai distributed; the English
  abstract, which ends in a Thai sentence, distributed with the paragraph; the section break
  after the keywords; links styled; H₂SO₄ and 10⁶ as subscript and superscript; the underlined
  word and `Ctrl + S`; the two footnotes at the foot of page 9 with their separator; the footer
  text; 25 pages.

The maintainer's judgement: works, no issues, in the layout the checklist asks for.

## 2. The fault

On page 9 of `sample-options`, the line before a hard break — "…เช่นเดียวกับข้อความ
ภาษาไทยทั่วไป", ending in two spaces in `thesis.md` line 67, which the fixture keeps to test
that a paragraph survives a hard break — was spread across the whole width one letter at a
time: "ภ า ษ า ไ ท ย ทั่ ว ไ ป". Word distributes a line that ends with SHIFT+RETURN unless the
document says otherwise, and `--align thai` sets every body paragraph to Thai distributed.
The package held the text correctly; the fidelity check could not see alignment.

## 3. The fix

With `--align thai`, `word/settings.xml` carries `<w:doNotExpandShiftReturn/>` as the first
child of `<w:compat>` — Word's "Don't expand character spaces on a line ending with
SHIFT+RETURN". Without the flag nothing is written, so three goldens keep their bytes.

- **Goldens rebuilt on purpose:** `sample-all-flags.docx` (`a1229587…d24337`) and
  `thesis-options.docx` (`10d32806…0e0410`); in each only `word/settings.xml` differs, and the
  JavaScript gives the same bytes. `thai_docx check` finds nothing in either.
- **Named test:** `test_thai_distributed_leaves_a_line_ending_in_a_manual_break_unspread`.
  Planted "never written": red in it, both goldens, and two neighbouring tests. Planted "always
  written": red in it and the three goldens built without `--align thai`.
- **Checklist:** `sample-options` now asks that the line before a hard break is not spread.

## Not proved here

- That Word for macOS (and Word 365 for Windows, which was not seen to spread the line on
  2026-09-16 but was not asked to look) now keeps the line: the rebuilt `sample-options` file
  must be opened again before the tag.
- The same spreading in a heading given `text-align: justify` or `thai-distribute` in the front
  matter together with `--chapter-title-on-new-line`, which also breaks a line: not written for,
  not seen.
- Google Docs, LibreOffice Writer and WPS Writer read `w:doNotExpandShiftReturn` their own way,
  if at all.
