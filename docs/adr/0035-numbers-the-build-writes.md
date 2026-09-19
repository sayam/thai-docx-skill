# 0035 — Every number the build can know is written as text, not left to the application

- Status: accepted
- Decided: 2026-09-19
- Extends: [0027](0027-lists-carry-entries-and-runs-name-their-font.md) (generated matter carries
  what an application would otherwise supply), [0021](0021-regions-sections-captions-and-lists.md)
  (which chose the fields this record replaces), [0012](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md)
  (five applications, Word 365 for Windows the reference)

## Where it came from

The five-application check of 2026-09-19 opened the release files in LibreOffice Writer
([record](../evidence/2026-09-19-three-of-five-applications.md)) and found, in a thesis whose
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

## Decision

**Every number the build can know is written into the document as text.** That is:

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

## What this gives up, plainly

**Word no longer renumbers.** A reader who opens the .docx and inserts a table, a chapter or a
list item gets no new numbers; the ones around it do not move. Until today Word did that.

This is the trade, and it is the right way round for this skill: the document is built from
Markdown, and a change belongs in the Markdown, where the build renumbers everything. The reader
who edits the .docx by hand is the second audience, not the first — and the first audience was
being handed `ตารางที่ บทนำ-ก`.

## Why not the alternatives

**Write literal numbers only under `--thai-digits`.** It would keep Word's renumbering where the
formats work, and it was tempting. Two reasons against: the caption fields are read wrongly by
LibreOffice whatever the digits are, so captions would have to change anyway; and a document
whose editing behaviour depends on a formatting flag is harder to explain than one rule that
always holds. One behaviour, in every document, is worth more than a saved feature in half of
them.

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
