# 2026-09-16 — the office check: what five applications showed, and the two faults it found

What this proves: the documents of `tools/oracle_set.py` were opened in the applications ADR
0012 names, by the maintainer, and what they showed was read against the checklist; two
faults in the package were found there and fixed (ADR 0027); the rest is recorded as the
limitations of the applications, with the evidence for each (gates
`release-oracle-set-is-the-goldens`, `build-faithful-and-byte-stable`).

Environment: the files `python3 tools/oracle_set.py` writes — every variant once per
application, byte for byte the goldens of `tests/golden/`. Opened in Microsoft Word 365 for
Windows (desktop) and Word on the web, Google Docs, LibreOffice Writer on Linux, and WPS
Writer. **Word for macOS was not opened**; it remains the one application of 0012 unchecked.
Content synthetic (ADR 0025 §10): `tests/fixtures/thesis/` and `tests/fixtures/sample.md`.

## 1. What the check found

| # | what was seen | where | what it was |
|---|---|---|---|
| 1 | every list — contents, tables, figures — showed its heading and a blank page | Word on the web, Google Docs, LibreOffice Writer, WPS Writer | **the package**: the field carried no result, and only Word on the desktop obeys `w:updateFields`. Fixed: the entries are written into the field (ADR 0027) |
| 2 | after a reader updated the fields, the entries came back in another font | Word on the web, LibreOffice Writer, WPS Writer | **the package**: the entries an application writes are hyperlink runs, and the `Hyperlink` style named no font. Fixed: it names one |
| 3 | chapter numbers as Latin letters ("ÓõõõyA ż" for "บทที่ ๑"), at the application's own size | WPS Writer | **the package, in part**: no numbering level named a font, size or `<w:cs/>`, and `Normal` leaned on `w:docDefaults`. Fixed: every level and `Normal` name them. The size is right afterwards; the letters are not — see 3 below |
| 4 | Thai distributed alignment, repeating table headers, F14 paper, cell margins, chapter and appendix headings, captions numbered by chapter | Word 365 desktop and web, Google Docs | correct |

## 2. What was right everywhere

The checklist items of ADR 0012 — content complete against the Markdown, bold and italic on
Thai, bullets and numbered lists, Thai line breaking inside words, the font applied, tables,
links and headings, footnotes at the foot of the page, images inside the page, ☐ and ☑ — held
in Word 365 desktop and web and in Google Docs. In LibreOffice Writer and WPS Writer they
held apart from the items named below.

## 3. The applications' own limitations, which no package can reach

- **WPS Writer draws Thai in `w:lvlText` through a legacy code page.** The chapter number
  reads as Latin letters however the level is written; the maintainer confirmed the font and
  size shown are the ones the file names, and that changing the document's font to Noto Serif
  Thai, Noto Sans Thai, FreeSerif or back to TH Sarabun New does not change it.
- **WPS Writer places SARA AM (ำ) wrongly**, in regular, bold and italic, in every font
  tried. The text in the package is one U+0E33 in a single run with `<w:cs/>` — the same
  bytes are right in Word, LibreOffice and Google Docs.
- **Google Docs converts a table of contents into its own object**, with its own font and its
  own page numbers.
- **A list is filled only when the reader updates fields**, outside Word on the desktop:
  Ctrl+Shift+F9 in LibreOffice Writer, References → Update in WPS Writer, the menu in Word on
  the web and Google Docs. The entries written into the field show without any of that; the
  page numbers do not.

## 4. Not proved here

- Word for macOS (ADR 0012's fifth application).
- The checklist as a filled table: this record is what was read, application by application;
  `.local/work/2026-09-16-oracle/CHECKLIST.md` is the maintainer's working copy and is not
  part of the repository.
- Whether Word's `thaiLetters` page numbering skips ฃ and ฅ as the build's own letters do.
