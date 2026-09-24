# 2026-09-22 — Word for macOS on the bytes for v0.2.0: the Thai default holds, and one item left undecided

> **Later:** §3 was settled the same day: `<w:cs/>` on Latin runs
> ([2026-09-22 Windows](2026-09-22-word-365-windows-on-the-release-bytes.md) §3, ADR 0039); Word for macOS has not read the
> ADR 0039 bytes ([2026-09-24](2026-09-24-what-v0.2.0-was-read-in.md)).

What this proves: the release documents of `tools/oracle_set.py`, built from `main` at `e9b5c0a`
and byte for byte the goldens of `tests/golden/`, were opened in Microsoft Word for macOS by the
maintainer, and what they showed was read against the checklist of ADR 0012. The two items this
release turns on — ADR 0038's default, which stopped writing `w:bidi="th-TH"`, and the section
break moved out of the table-of-contents field — both hold. No fault in the package was found.
One checklist item is not decided and is recorded as such here (gates
`release-oracle-set-is-the-goldens`, `build-faithful-and-byte-stable`).

Environment: Microsoft Word for macOS, the same very old installation as
`2026-09-17-word-for-macos.md` — it opens the files read-only, and from `sample-layout` onward it
also showed the banner "View Only — your account doesn't allow editing on a Mac". Four documents,
opened with formatting marks shown: `sample-options` (26 pages), `sample-text` (24),
`sample-layout` (27), `sample-basic` (2). `sample-auto` is not in this application's scope — it is
built for Word on the Windows desktop. Read from 28 screenshots the maintainer took, one at a time.
Content synthetic (ADR 0025 §10): `tests/fixtures/thesis/` and `tests/fixtures/sample.md`.

## 1. The two items this release turns on

**No red underline under a correctly spelled Thai word.** Across every page of Thai in all four
documents there is none — the abstract and body of `sample-text` and `sample-options`, the chapter
and section headings, the tables, the appendices, the bullet and task lists of `sample-basic`.
ADR 0038 wrote the condition that would flip the default back: an application underlining correctly
spelled Thai because the document no longer names its complex-script language. **On this machine
that condition did not trigger.** The machine has Thai among its languages, which is what the
default relies on and what §3 of `references/limits.md` tells the reader.

**SARA AM sits over its own letter** — `กำหนด`, `ทำให้`, `คำไทย`, `สำคัญ`, `ข้อกำหนด`. This is what
the default buys, and what `--thai-language` costs in WPS Writer.

**The section break is outside the field.** In every front-matter list — contents, list of tables,
list of figures — `Section Break (Next Page)` is drawn after the list's entries, not inside them.
That is the fix of `2026-09-20-the-field-keeps-nothing-of-the-section.md` seen in the application.
It was read in eight of the screenshots, across `sample-options`, `sample-text` and `sample-layout`.

## 2. What else was right

Read against the checklist of ADR 0012:

- Content complete against the Markdown; bold and italic render on Thai (`ปัญหาสำคัญ` bold, the
  quoted passage italic); bullets show as •; numbered lists count on, including a nested level.
- Thai lines break inside words, not only at spaces, through the long distributed paragraphs.
- The font the file names is used throughout; tables, links and headings are correct; images stay
  within the page — the two charts, the flow diagram and the scaled image of `sample-basic`.
- `□` and `■` show as squares, not as blank space (ADR 0033), in the task lists of `sample-basic`,
  `sample-text` and `sample-options`.
- No "Compatibility Mode" in the title bar; the status bar shows **Thai** in every screenshot.
- Numbering follows the flags: `บทที่ ๑`, `๑.๑`, `ตารางที่ ๑-๑` and Thai page numbers under
  `--thai-digits`; `ก ข ค` front-matter numbering without it; `Appendix A` and `ตารางที่ A-๑` under
  `--appendix-label Appendix --appendix-numbers upper-letters`, against `ภาคผนวก ข` and
  `ตารางที่ ข-1` where those flags are absent.
- `--hide-spelling-errors` works, shown by contrast rather than by assertion: `sample-layout`
  carries no squiggle of any kind while `sample-basic`, opened in the same session on the same
  machine, carries several.

## 3. The item not decided

**Correctly spelled English words carry red squiggles**, worst in the English abstract of
`sample-text` and `sample-options`, where nearly every word of the paragraph is underlined, and
scattered elsewhere (`Office`, `Open`, `complex script`, `code span`, `hard break`,
`Setext heading`, and the English title page of `sample-text`). ADR 0012's Word-only item is
"no squiggles under correctly spelled words", and these are correctly spelled.

**It is not what ADR 0038 changed.** The documents still write `<w:lang w:val="en-US"/>` on every
run — 497 of them in `sample-text-word_mac.docx`, 75 in `sample-basic-word_mac.docx` — beside the
`<w:cs/>` marker. What ADR 0038 stopped writing is `w:bidi`, which names the complex-script
language and reaches no Latin run. The Latin language this file declares is the same as it has
always been.

**It is not yet known whether this is the application, the machine, or the package**, and the
maintainer has deferred the two checks that would settle it to roughly 2026-10-06. Those checks
are: whether an English (US) proofing dictionary is installed on that machine, and what
Tools → Language reports for the abstract's paragraph. Until then this item is **undecided**, not
failed, and it is not yet an accepted limitation: `docs/rules.md` allows a deviation only with a
record naming the cause and why an attribute cannot reach it, and neither is known here. It does
not bear on the Thai default, which is what this release changes.

## 4. Not proved here

- **Word 365 for Windows, Word on the web, LibreOffice Writer, Google Docs and WPS Writer** on
  these bytes. ADR 0012 makes Word 365 for Windows the reference that must pass every item, and it
  has not been opened on this build. This record is one application of the five; the release's
  limitation record is not complete until the other four are read.
- **`sample-auto`** — built for the Windows desktop, outside this application's scope.
- **Anything that needs editing.** This installation opens the documents read-only, so the theme
  check (type a Latin word into a paragraph the build wrote, insert a table from the ribbon, and
  see the document's own font) could not be done, and neither could the **double field update**
  that `2026-09-20-the-field-keeps-nothing-of-the-section.md` still owes. That update belongs to
  Word for the web in any case.
- **Footnotes at the foot of the page.** `sample-basic` carries a footnote reference in its text,
  but no screenshot shows the foot of that page. The item held in this application on 2026-09-17
  (`2026-09-17-word-for-macos.md`, two footnotes at the foot of page 9 of `sample-options`) and
  nothing in this release touches footnotes, but it was not re-read on these bytes.
- **Two faint marks** under `วิทยาศาสตรมหาบัณฑิต` and `ฟอนต์` that the screenshots have too few
  pixels to settle. If `ฟอนต์` is underlined it is not a fault: it is a loanword absent from the
  Thai dictionary, and its being marked would show that Thai proofing is running, which is what the
  default depends on.

The screenshots are the maintainer's working copy and are not part of the repository; they are kept
with the checklist at `.local/work/2026-09-22-release-check/`, with the item-by-item reading in
`RESULTS-word_mac.md`.
