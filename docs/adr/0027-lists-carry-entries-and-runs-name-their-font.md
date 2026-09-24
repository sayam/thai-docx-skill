# 0027 — Generated matter carries what an application would otherwise supply: list entries, and a font on every run

- Status: accepted
- Decided: 2026-09-16
- Amended by: [0038](0038-the-thai-language-is-written-only-when-asked.md) (`w:lang w:bidi` only with `--thai-language`; WPS's SARA AM traced to that attribute), [0039](0039-complex-script-is-marked-where-it-is.md) (`<w:cs/>` only on complex-script runs, none in `Normal`)

## Where it came from

The office check of ADR 0012 was run by the maintainer on 2026-09-16 in Word 365 for
Windows (desktop and web), Google Docs, LibreOffice Writer and WPS Writer. Word on the
desktop was right; the other four showed two faults the file itself caused.

**A list with nothing in it.** `<!-- toc -->`, `<!-- list-of-tables -->` and
`<!-- list-of-figures -->` were written as a field with an empty result: `begin`, the
`TOC` instruction, `separate`, `end`. Word on the desktop obeys `w:updateFields` and fills
it in when the file opens; Word on the web, Google Docs, LibreOffice Writer and WPS Writer
do not, and every list showed its heading with a blank page under it — a thesis whose
contents page is empty.

**Text drawn in another application's font.** WPS Writer showed the chapter number of every
heading as Latin letters ("ÓõõõyA ż" for "บทที่ ๑") and, when the number was selected, its
own default size. The numbering levels in `word/numbering.xml` named no font, and the style
`Normal` named none either — both leaned on `w:docDefaults`, which WPS reads after the
styles rather than under them. The same hole let a list an application rebuilt come back in
another font: the entries it writes are hyperlink runs, and the `Hyperlink` style named no
font.

## Decision

**A generated list carries its entries.** Between `separate` and `end` the build writes one
paragraph per entry — `TOC1`, `TOC2` or `TOC3` — holding the entry's text: a heading of
level 1 to 3 with the number Word would give it ("บทที่ 1 บทนำ", "ภาคผนวก ก แบบสอบถาม"), or
a caption ("ตารางที่ 1-1 ผลการสำรวจ") for a list of tables or figures. The field opens in the
first entry and closes in the last, as Word writes it itself. `w:updateFields` stays, so
Word replaces the entries with its own when the file opens.

**No page numbers are written.** Which page an entry falls on is known only to a layout
engine. The entries carry text alone; an application that rebuilds the list adds the numbers,
and one that does not shows a list that is right about what the document holds and silent
about where. A number the build guessed would be a number the reader could not trust.

**Every run the build generates names its font, size and complex-script flag.** That is:
each of the nine levels of every numbering definition (bullets, ordered lists, chapter and
appendix numbers), the `Hyperlink` character style, and the `Normal` style, which now
repeats what `w:docDefaults` already says. `<w:cs/>` and `w:lang w:bidi` go with the font
wherever Thai can appear, because a run without them is measured as Latin text.

**The reference for fidelity is unchanged (0023).** The entries are generated matter, like a
caption's label and number: `expected_text()` builds the same list, so the build still
refuses a document that differs from the Markdown.

**Thai distributed is for Thai.** `--align thai` fills a line by spreading what is on it,
which is how Thai is set — it has no spaces between words. A paragraph with no Thai
character in it keeps the ordinary left alignment instead, so an English reference does not
come out as "( 2 0 2 4 a)" and an English title does not stretch across the page. This holds
for body paragraphs, list items, quotations, footnotes, table cells, captions and the entries
written into a list; a paragraph that already sets its own alignment keeps it. Alignment
only: not one character changes (0023).

**A chapter title may start its own line.** `--chapter-title-on-new-line` puts a line break
before the heading's own text in the chapters and the appendices, so the number Word writes
("บทที่ 1", "ภาคผนวก ก") keeps the first line and the title starts the next, as a Thai thesis
sets it. OOXML gives a numbering level no such suffix — nothing, a space or a tab — so the
break belongs to the heading. The entries written into a list fold it back to one line. The
flag is off by default, and a document with no region comment is told the flag changed
nothing rather than left to wonder.

Left out on purpose:

- Page numbers in the written entries, and `PAGEREF` fields with a guessed result.
- Hyperlinks and bookmarks in the written entries: an application that rebuilds the list
  makes its own, and one that does not would gain links to nowhere.
- Writing the chapter number as text in the heading instead of as numbering. It would show
  in WPS, and it would break the numbering Word rebuilds the list from.

## Why

A list is the one part of a .docx whose content is normally left to the reader's
application, and four of the five applications of 0012 leave it empty. Writing the entries
costs the document nothing in Word, where they are replaced, and gives every other
application a contents page that is worth reading. The cost is that a reader who never
updates the fields sees no page numbers — a lack, not an error, and the honest half of what
the build can know.

Naming the font on generated runs is the same rule the applied styles already follow
(0012's check found the table of contents in Angsana New 20 pt when Word supplied the style).
Inheritance an application does not perform is inheritance the file cannot rely on.

## Expires when

A layout engine is part of the build, or the applications of 0012 agree on updating fields
when a file opens.

## Known limitations found in the same check, which no file can fix

- **WPS Writer** draws Thai in `w:lvlText` through a legacy code page, so any chapter or
  appendix number in Thai is unreadable there whatever font the level names; and it places
  SARA AM (ำ) wrongly in every weight and every Thai font tried. Both are WPS's rendering,
  not the package: the same bytes are right in Word, and the text in the file is a single
  U+0E33 in one run.
- **Google Docs** converts a table of contents into its own object, with its own font.
- **Word on the web, Google Docs, LibreOffice Writer and WPS Writer** fill a list only when
  the reader updates fields (Ctrl+Shift+F9 in LibreOffice, References → Update in WPS).
