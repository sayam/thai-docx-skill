# 0021 — Reports and theses: regions, a section per chapter, numbered captions and lists

- Status: accepted
- Decided: 2026-09-16

## Where it came from

With heading numbers and heading styles in place, the maintainer asked for what a Thai
report or thesis needs: a chapter heading that reads "บทที่ 1", table and figure captions
numbered by chapter — "ตารางที่ 1-1", "รูปที่ 2-1" — gathered into a list of tables and a
list of figures, and a next-page section break closing every chapter and every page
before and after the chapters: cover, acknowledgements, table of contents, abstract,
bibliography, appendices.

Markdown has none of this. The maintainer chose, among options put as choices: comments
that mark the regions of the document; `Table:` and `Figure:` paragraphs for captions;
comments where the lists go; a chapter heading on one line; front pages counted ก ข ค and
the chapters from 1; the chapter number whenever there are chapters; and a document
without region comments built exactly as before. Asked next for a choice of numbers before
the chapters and for lettered appendices, the maintainer chose i ii iii, I II III and
1 2 3 beside ก ข ค; an appendices region; A B C, 1 2 3 and I II III beside ก ข ค; and
captions in an appendix numbered by it.

## Decision

**Regions.** Four comments, each alone on its line at the top level of the document, in
this order: `<!-- front -->`, `<!-- chapters -->`, `<!-- back -->`,
`<!-- appendices -->`, and `<!-- back -->` once more after the appendices — each at most
once, any left out. What comes before the first is the cover. A region comment given
twice or out of order stops the build with its line. Every other comment still renders
nothing (0010) — but one that looks meant as a region or list comment and is not taken
warns with its line: the same but for case or spacing (`<!-- Chapters -->`), a known slip
(`chapter`, `appendix`), one letter off a short name or two off a long one, or a right
one inside a list, quotation or footnote.

**Sections.** When a document has a region comment, a next-page section starts at each
region comment and at each `#` heading, except where the section so far is empty. A
section closes in the properties of its last top-level paragraph, never in an empty
paragraph that could spill onto a page of its own. Page numbers:

- the cover has none — its header and footer are the plain ones, text without the number;
- the front pages count ก ข ค (`thaiLetters`) from the first, or, with
  `--front-page-numbers`, i ii iii (`lower-roman`), I II III (`upper-roman`) or 1 2 3
  (`decimal`, Thai digits with `--thai-digits`);
- the chapters start again at 1, and the back and appendix pages go on from there
  (`decimal`, or Thai digits with `--thai-digits`);
- `--no-page-number-first` leaves the first page of every section without its number.

**Chapters.** In `<!-- chapters -->`, a `#` heading is numbered by Word as
`--chapter-label` and the number on one line — "บทที่ 1 บทนำ" — whether or not
`--heading-numbers` is given; with it, `##` and below read 1.1, 1.1.1. Headings in the
cover, front and back regions have no number (`w:numId` 0 on the paragraph). The heading
text is not changed.

**Appendices.** In `<!-- appendices -->`, a `#` heading reads `--appendix-label` (default
ภาคผนวก) and its number — ก ข ค by default, or with `--appendix-numbers` A B C
(`upper-letters`), 1 2 3 (`decimal`) or I II III (`upper-roman`) — from a numbering list of
its own, set on each heading paragraph so Heading 1 stays the chapters'; with
`--heading-numbers`, `##` reads ก.1. Letters run ก ข ค ง จ … ฮ without ฃ and ฅ, and A to Z
then AA, as the build writes them into caption numbers.

**Captions.** A paragraph that opens with plain `Table:` directly before a table, or with
`Figure:` directly after a paragraph holding only an image, is that table's or figure's
caption; the prefix and the space after it are removed. The caption reads its label
(`--table-label`, default ตารางที่; `--figure-label`, default รูปที่), then its number,
then the text:

- in the chapters and the appendices, the chapter or appendix number, `-`, and a count
  that starts again at every `#`: `STYLEREF 1 \s` and `SEQ Table \s 1` — "ตารางที่ 1-1",
  "ตารางที่ ก-1";
- elsewhere in a document with regions, the count alone, starting again at every `#`;
- without region comments, one count through the document: `SEQ Table`.

The fields carry their results as the build counts them, so an application that never
updates fields shows the right numbers. Label and number are bold; a table caption keeps
with its table and a figure keeps with its caption, which is centred. A `Table:` or
`Figure:` paragraph anywhere else stays text, with a warning naming its line; so does
`Figure:` on the line under its image with no blank line between (one paragraph), and
`Table:` on the line under its table (GFM makes it the table's last row).

**Lists.** `<!-- toc -->`, `<!-- list-of-tables -->` and `<!-- list-of-figures -->`, alone
on a line at the top level, become the table of contents, `TOC \c "Table"` and
`TOC \c "Figure"` at that place; the author writes the heading above them. Word is asked
to update fields when the file opens. `--toc` still puts a table of contents first.

**Fidelity.** The text check (0016) reads a caption as label, number and caption text,
computed from the Markdown by the same rules; every other paragraph is unchanged. Styles
Word applies itself — Caption, table of figures, TOC 1–3 — carry the document's font and
size.

Left out on purpose:

- A chapter heading on two lines ("บทที่ 1", then the title): a line break inside the
  heading is content the Markdown does not have.
- Captions after a table, or taken from an image's alt text, as Pandoc allows [S40]: one
  place for each keeps the rule short; `Figure:` is this skill's, not Pandoc's.
- Figures numbered inside the front pages; appendix letters other than the four styles.
- Region comments inside lists or quotations, or on a line with text.

## Why

Word already has every piece: sections carry their own page numbering, numbering lists
carry the chapter label, SEQ and STYLEREF fields number captions by chapter, and
`TOC \c` builds the lists [S7]. Comments are the one Markdown construct that renders
nothing in every other reader, so the file stays readable Markdown. Writing the field
results in keeps the numbers right in LibreOffice and Google Docs, which do not update
fields; asking Word to update fills in the page numbers only it can know. A document
without region comments keeps its bytes, so nothing built before changes.

## Expires when

Documents need more than one chapter level, parts or volumes, or a caption placement
other than Thai convention — or Word shows `thaiLetters` page numbers with ฃ or ฅ, which
would part the page numbers from the appendix letters.
