# 2026-09-22 — Word 365 for Windows on the bytes for v0.2.0: everything but one item, and that item is ours

What this proves: the release documents of `tools/oracle_set.py`, built from `main` at `e9b5c0a`
and byte for byte the goldens of `tests/golden/`, were opened in Microsoft Word 365 for Windows —
the reference application of ADR 0012 — and read against that record's checklist. Everything this
release turns on holds. **One item fails: correctly spelled English words carry red underlines.**
This record establishes that the failure is in the package, that it is not new in this release, and
that an attribute reaches it — which is why it is a defect to be fixed by
[ADR 0039](../adr/0039-complex-script-is-marked-where-it-is.md) and not a limitation to be
recorded. Three parts of the checklist were not read and are named in §5, so this is not yet a
statement that the application passes (gates `release-oracle-set-is-the-goldens`,
`build-faithful-and-byte-stable`).

**These bytes do not survive ADR 0039.** That record changes every document in the set, so this
reading will have to be done again before the tag. It stands as the reading of the bytes it names,
and as the measurement that sent the release back to the code.

Environment: Microsoft Word 365 for Windows, on the maintainer's Windows machine, which has Thai
among its languages. Five documents, opened with formatting marks shown: `sample-options`,
`sample-layout`, `sample-text`, `sample-basic`, and `extra-sample-text-with-thai-language` — the
last built on purpose with `--thai-language`, which is not in the release set but is what makes §3
conclusive. Read from 30 screenshots the maintainer took; **three of them are screenshots of a
terminal and are not evidence**, leaving 27. Content synthetic (ADR 0025 §10):
`tests/fixtures/thesis/` and `tests/fixtures/sample.md`.

## 1. The two items this release turns on

**No red underline under a correctly spelled Thai word**, in every screenshot that carries Thai,
across all five documents. This is the condition ADR 0038 named as the one that would flip its
default back, and on the reference machine it did not trigger.

**SARA AM sits over its own letter** — `กำหนด`, `ทำให้`, `คำไทย`, `สำคัญ`, `ข้อกำหนด`, clear in
every screenshot. This is what the default buys and what `--thai-language` costs in WPS Writer.

**The section break is outside the table-of-contents field**, in nine screenshots (09, 11, 14, 18,
23, 25, 27, 28, 30): `Section Break (Next Page)` is drawn after the list's entries, never among
them. That is the fix of `2026-09-20-the-field-keeps-nothing-of-the-section.md`, seen in the
reference application.

**Updating the fields gives the right page numbers.** Screenshot 05 shows the front matter before
the update, every line reading `1` or `ก`; screenshots 06 and 07 show it after, reading `ก ข ค ง ฉ ช`
and `12 13 14 15 16 17`. The earlier record owes this check in Word for the web, where a *double*
update is needed; here a single update was enough.

## 2. What else was right

- Content renders complete where the screenshots reach; bold and italic on Thai (`ปัญหาสำคัญ` bold,
  `เส้นหยักสีแดง…` italic, screenshot 19); bullets as •; numbered lists count on, in both Arabic
  and Thai digits.
- Thai lines break inside words through the long distributed paragraphs.
- **Footnotes sit at the foot of the page and are numbered `๑` and `๒` in Thai digits**
  (screenshot 20), below their separator. This item could not be read on macOS.
- The font box reads **TH Sarabun New** in every screenshot; no "Compatibility Mode" in the title
  bar; the status bar reads Thai.
- Tables, links (`ECMA-376`, `https://example.com/thai-docx`) and headings correct; images within
  the page; `□` and `■` drawn as squares (ADR 0033) in screenshots 02, 22 and 25.
- Subscript, superscript, strikethrough and code spans: H₂O, x², H₂SO₄, 10⁶.
- Numbering follows the flags: `บทที่ ๑`, `๑.๑`, `ตารางที่ ๑-๑`, `รูปที่ ๒-๑` and a Thai page
  number `๑๐` under `--thai-digits`; `A.๒` and `ตารางที่ A-๑` under `--appendix-numbers
  upper-letters`.
- **`--hide-spelling-errors` works, and the application says so itself**: on `sample-layout` Word
  raised its own banner — *"TURN ON PROOFING — Spelling and grammar errors aren't being checked in
  this document."*

## 3. The item that fails, and why it is ours

**Correctly spelled English words carry red underlines.** Worst in the English abstract, where
nearly every word of the paragraph is underlined — `This study develops … evaluates … builder …
turns … documents written … Documents produced …` — in `sample-options` (screenshot 15),
`sample-text` (27) and `extra-sample-text-with-thai-language` (30). Also the English title
(screenshot 28) and, scattered through every document, `Markdown`, `Office`, `Open`,
`complex script`, `code span`, `hard break`, `macOS`, `LibreOffice`, `Docs`.

ADR 0012's Word-only checklist item is *"no squiggles under correctly spelled words"*, and these
are correctly spelled. `docs/rules.md` makes a deviation unacceptable *"when the reference
application fails"*. So this is a failure, and the only question worth asking is where the cause
lives. Three measurements answer it.

**It is not what ADR 0038 changed.** `extra-sample-text-with-thai-language` still writes
`w:bidi="th-TH"`, and it is underlined exactly like the four that do not (screenshot 30). Both
settings of the attribute this release changed give the same result.

**It is not new in this release.** The set was built again from the tag `v0.1.1` (`9325c47`) inside
an incus container and compared run by run against `main`. The English abstract is one run in both,
and one attribute apart:

| | `w:rPr` of the English abstract's run |
|---|---|
| v0.1.1 | `<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>` |
| this release | `<w:cs/><w:lang w:val="en-US"/>` |

`<w:cs/>` is in both. Counting the whole file: v0.1.1 has 584 runs, 584 carrying `<w:cs/>`, of
which 249 contain no Thai character at all; this release has 497 runs, 497 carrying it, 231 of them
with no Thai. **Every run is marked complex script whether or not it holds any.** That is cause 2
of ADR 0004 as it was written, and it predates v0.1.0.

**It is in the package, and an attribute reaches it.** The maintainer typed `(Test Add Text)` into
the middle of the same English abstract in Word. The typed words carry no underline; the words the
build wrote, on the same line of the same paragraph on the same machine, do. Word writes no
`<w:cs/>` when a person types Latin text. On a Latin-only run the element tells Word to proof
English with a complex-script language, and no complex-script language spells English.

Both conditions `docs/rules.md` sets for an acceptable deviation therefore fail: the reference
application does have it, and our attributes do reach it. It is a defect. ADR 0039 fixes it, and
`2026-09-22-what-word-writes-when-a-person-types.md` is the measurement it copies.

This settles what `2026-09-22-word-for-macos-on-the-release-bytes.md` §3 left undecided, and
settles it earlier than the checks that record deferred.

## 4. Two things that are not faults

**The status bar reads "English (United States)" in screenshots 08 and 25.** In both, the cursor
sits on a line of Latin characters such as `ตารางที่ A-๑`. Word reports the language of the run
under the cursor; in Thai body text it reads Thai.

**`ฟอนต์` and `วิทยาศาสตรมหาบัณฑิต` carry red underlines** (screenshots 20, 28). A loanword and a
compound absent from the Thai dictionary. Not a fault — and useful, because it shows Thai proofing
is actually running, which is what ADR 0038's default depends on. The same two words were seen on
macOS.

## 5. Not read here

1. **`sample-auto`, all eight of its items.** The maintainer had not added it to the set at the
   time of reading. This is the only application in which those items can be checked at all.
2. **The theme item** — type a Latin word into a paragraph the build wrote, insert a table from the
   ribbon, and see the document's own font in both. Not done.
3. **Content complete against the Markdown**, item by item. The screenshots do not cover every page
   of every document, so this is "nothing wrong was seen", not "everything was checked".
4. **The other four applications** on these bytes. Word for macOS has its own record; Word for the
   web, LibreOffice Writer, Google Docs and WPS Writer have not been opened on this build.

The screenshots are the maintainer's working copy and are not part of the repository; they are kept
with the checklist at `.local/work/2026-09-22-release-check/`, with the item-by-item reading in
`RESULTS-word365_windows.md` and the v0.1.1 comparison in `.local/work/2026-09-22-v011-compare/`.
