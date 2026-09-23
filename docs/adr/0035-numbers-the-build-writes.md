# 0035 — Every number the build can know is written as text, not left to the application

- Status: superseded
- Decided: 2026-09-19
- Superseded by: 0036
- Extends: [0027](0027-lists-carry-entries-and-runs-name-their-font.md) (generated matter carries
  what an application would otherwise supply), [0021](0021-regions-sections-captions-and-lists.md)
  (which chose the fields this record replaces), [0012](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md)
  (five applications, Word 365 for Windows the reference)

## Where it came from

The five-application check of 2026-09-19 opened the release files in LibreOffice Writer (its
record was not kept: PR #54 was closed for what else it said) and found, in a thesis whose
numbers Word draws correctly:

| what Word and WPS draw | what LibreOffice drew |
|---|---|
| `บทที่ ๑`, `๑.๑`, `๒.๑` | `บทที่ 1`, `1.1`, `2.1` |
| `๑.` `๒.` `๓.` in a numbered list | `1.` `2.` `3.` |
| `ตารางที่ ๑-๑` | **`ตารางที่ บทนำ-ก`** |
| `รูปที่ ๒-๑` | **`รูปที่ ทฤษฎีและงานวิจัยที่เกี่ยวข้อง-ก`** |

Three causes, all in the same place — a number the file asked an application to work out:

- `<w:numFmt w:val="thaiNumbers"/>` is a format LibreOffice does not implement, so headings and
  ordered lists came out in Latin digits.
- `STYLEREF 1 \s` — "the number of the nearest Heading 1" — returned the heading's **text**.
- `SEQ Table \* ThaiArabic \s 1` returned a Thai **letter** and ignored the restart.

The maintainer's judgement, and the reason this is a decision and not a note: *a document that
looks like that is not usable, and a skill whose output is not usable is the same as no skill at
all. For work published for other people, what serves the most readers comes first.*

## What was measured, again, on 2026-09-19

The first shape of this record wrote every number as text, in every document. The maintainer
asked the question that shape could not answer: *a person who edits the .docx afterwards — do
they renumber by hand?* They do, and that is a real cost, so it is only worth paying where it
buys something.

A probe document with one heading list per numbering format, converted by LibreOffice 26.8 to
ODT, says what it reads each format as:

| `w:numFmt` | LibreOffice reads it as |
|---|---|
| `thaiNumbers` | `num-format="1"` — **Arabic** |
| `custom` with `w:format="๑, ๒, ๓, …"` | not read at all; the prefix is lost too |
| `thaiLetters` | `num-format="ก, ข, ค, ..."` ✓ |
| `upperLetter`, `upperRoman`, `lowerRoman`, `decimal` | `A`, `I`, `i`, `1` ✓ |

**`thaiNumbers` is the only format it cannot draw.** Everything else this skill asks for, it
draws correctly.

## Decision

**One answer for the whole document, never a number here and a field there.** A document that
renumbers its headings but not its captions goes wrong silently the first time a reader inserts a
chapter — `ตารางที่ 1-1` sitting in chapter 2, with nothing to say so. That is a worse thing to
hand someone than a document they must renumber by hand.

**The build writes every number itself when anything in the document needs a format or a field
the five applications do not agree on.** Two things do:

- **`--thai-digits`**, because `thaiNumbers` is drawn as 1, 2, 3 by LibreOffice;
- **regions** (`<!-- chapters -->` and the rest), because a caption inside chapters takes its
  number from `STYLEREF 1 \s`, which LibreOffice answers with the chapter's *title*, and from a
  `SEQ` whose restart at each chapter it ignores.

**A document with neither keeps the applications' own numbering, whole** — headings, ordered
lists and captions alike, each renumbering itself as a reader edits, which is what those
applications are for.

What the build writes, where it writes:

- **a heading's number** — `บทที่ ๑`, `๑.๑`, `๑.๓.๒`, `ภาคผนวก ก`, `A.๑`, `1.` — a run in the
  heading's own paragraph, carrying no run properties, so it takes the heading style's;
- **an ordered list's marker** — `๑.` and a tab, with the hanging indent the numbering level had;
- **a caption's number** — `ตารางที่ ๑-๑` — beside its label, in one bold run.

**What the build cannot know stays a field or a format**, because only a laid-out page has it:
page numbers (`PAGE`, `w:pgNumType`), footnote marks, and the page numbers a table of contents
shows after an application updates it.

**A bullet stays a numbering level.** `•` is a literal `w:lvlText` — there is no format to
compute, and every application drew it correctly.

`word/numbering.xml` therefore holds one list: the bullet.

**The three lists stay `TOC` fields, and a caption takes a style of its own.** A list of tables
was `TOC \h \z \c "Table"`, and `\c` collects the `SEQ` fields a caption used to carry: with the
number written as text there was nothing left to collect, and LibreOffice emptied both caption
lists the moment a reader updated the fields. The answer is not to stop using a field — a field is
what every application, and every person who edits the file afterwards, knows how to update. It is
to collect something the build still writes: each caption takes a paragraph style of its own,
`Table Caption` or `Figure Caption`, and the list collects that style with `\t`. LibreOffice reads
it as its own index-by-style, which is what it is.

## What this gives up, plainly, and where

**In a thesis — anything with regions — and in any document in Thai digits, nothing renumbers
itself.** A reader who inserts a chapter, a table or a list item renumbers by hand from there,
and the guide says so rather than letting them find out. The way back is the one the skill was
built for: change the Markdown and build again, where every number is worked out afresh.

**In a report with neither, nothing is given up at all.** Word numbers it, Word renumbers it, and
the five applications agree.

The trade is made per document and only where it buys something, because a document whose
numbers an application cannot draw is worse than one a reader must renumber — and a document
that renumbers half of itself is worse than both.

## Why not the alternatives

**Write literal numbers in every document, for one rule that always holds.** That was the first
shape of this record, and it was wrong: it took automatic renumbering away from documents that
never had a problem, to buy a consistency only the maintainer would notice. The rule that
survives is nearly as short — *the build writes a number the application cannot draw* — and it
costs nothing where nothing is wrong.

**Keep the fields and record the difference.** That is what ADR 0012 says to do when an
application draws its own way — and it is right when a reader sees something *different*. Here a
reader sees something *wrong*: a caption that names a chapter instead of numbering it is not a
rendering difference, it is a document nobody can hand in.

**Ask LibreOffice to fix it.** Worth doing, and it changes nothing for the person whose thesis is
due. A file that states its numbers needs no application to agree with it.

## What it costs

**The bytes of every document change**, and they get smaller: the heading and ordered-list
numbering definitions are gone. The five goldens shrank by about 11%. The five applications of ADR
0012 are due another look before the release, and this record is the reason.

The build's text now contains the numbers, so `plain_text`, the fidelity check and `check`'s
text comparison all account for them — a number is generated matter, like a caption's label, and
[ADR 0023](0023-fidelity-transformations-restated-again.md) still governs the author's own words,
which are untouched.

Two settings changed what they depend on: `--chapter-label` and `--appendix-label` now say they
changed nothing unless a heading actually carries a chapter number or an appendix letter, which is
what they had always meant.

## Expires when

LibreOffice implements `thaiNumbers`, `STYLEREF \s` and `SEQ \* ThaiArabic` as Word does — and
even then, only if automatic renumbering is worth more to this skill's readers than a file that
says what it means.
