# 2026-09-17 — Word for macOS: the fifth application, a line spread letter by letter, and a chapter number at the body's size

What this proves: the release documents of `tools/oracle_set.py` were opened in Microsoft Word
for macOS, the one application of ADR 0012 left unchecked on 2026-09-16
(`2026-09-16-office-check-five-applications.md`); what it showed was read against the
checklist; one fault in the package was found there and fixed, and the fix is held by a named
test as well as the goldens (gates `release-oracle-set-is-the-goldens`,
`build-faithful-and-byte-stable`).

Environment: Microsoft Word for macOS — a very old version that opens the files read-only —
and, for the re-checks, Word 365 for Windows; Thai proofing language; the files of `main` at
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

## 4. The re-check, and a second fault

The rebuilt `sample-options` was opened again in Word for macOS and Word 365 for Windows: the
line before the hard break stays as written in both (maintainer, 2026-09-17).

In the same files the maintainer found the number Word draws for a chapter heading — "บทที่ ๑"
before "บทนำ" — at 16 pt, the body's size, beside a 20 pt title; Word 365's font box showed 16
on the number and 20 on the title. The fault was the package's, from ADR 0027: every numbering
level named a font and size so that WPS would not fall back to its own, and every level named
the *body's*. A level's run properties override the paragraph's style for the number, so
heading numbers lost the heading's size, and would have lost a front matter font, colour or
underline too.

**The fix:** the levels of the heading numbering (chapters and `--heading-numbers`) and of the
appendices take their heading's run properties — the built-in look with what `heading-n`
in the front matter changes, the same computation the heading style is written from — and
still name a font (the heading's, or the document's). Lists keep the body's; levels past
Heading 6 keep the body's.

- **Goldens rebuilt on purpose:** `thesis-text.docx`, `thesis-options.docx`,
  `thesis-layout.docx`; in each only `word/numbering.xml` differs (the chapter level now
  `<w:b/><w:bCs/><w:sz w:val="40"/>`), and the JavaScript gives the same bytes. The two
  sample goldens keep theirs: the heading styles are written byte for byte as before.
- **Named test:** `test_every_generated_run_names_the_font` now holds the list levels to the
  body, the heading levels to their heading (a `heading-1` with a font, 22 pt, a colour and an
  underline included, compared with the Heading 1 style), and levels past Heading 6 to the
  body. Planted "heading levels take the body's look": red in it and the three thesis goldens.
  Planted "the front matter font ignored on the number": red in it alone.
- **Checklist:** `sample-text` asks that the chapter number is the chapter title's size.

## 5. The heading-number fix, seen

The files rebuilt for section 4 were opened in Word 365 for Windows and Word for macOS: "บทที่ ๑"
and "๑.๑" are their titles' size and weight in both; Word 365's font box shows TH Sarabun New
20 pt, bold, on the number as on the title (maintainer, 2026-09-17).

In Word for macOS the number's face looked slightly unlike the title's. By the package they
are one face: Heading 1 names no font and inherits TH Sarabun New from `Normal`, and the level
names TH Sarabun New. The one difference in the XML is that a numbering level's `w:rFonts`
names three slots and `Normal`'s four (no `w:eastAsia` on the level); a probe pair differing only
in that was built (`.local/work/2026-09-17-font-probe/`) and not opened. The Word for macOS at
hand is a very old version that opens these files read-only and shows no font properties, so
the maintainer decided that **Word 365 for Windows is the reference** for the face, and the
observation stays unexplained rather than a reason to change bytes.

## Not proved here

- Why the number's face looked unlike the title's in the old, read-only Word for macOS
  (section 5), and whether a current Word for macOS shows it.
- WPS Writer after either fix.
- The same spreading in a heading given `text-align: justify` or `thai-distribute` in the front
  matter together with `--chapter-title-on-new-line`, which also breaks a line: not written for,
  not seen.
- Google Docs, LibreOffice Writer and WPS Writer read `w:doNotExpandShiftReturn` their own way,
  if at all.
