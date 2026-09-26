# 2026-09-23 — editing in Word 365 for Windows after the build

What this proves: in Word 365 for Windows, a reader who edits a built document can add a table
or a figure and have it join the lists, in both kinds of document, by the route
`references/limits.md` §6 gives each; and a chapter inserted inside the first chapter's section
restarts the page count, which one setting undoes. What it does not prove: anything in another
application, Word for the web included — its section breaks and Format Painter were not read.

Environment: Word 365 for Windows, read by the maintainer on 2026-09-23. Files: the release
oracle set on the bytes of ADR 0039 — `sample-options` (the ready-to-use thesis) and
`sample-auto` (the same with `--auto-numbering`), built by `tools/oracle_set.py`; the corrected
`sample-auto` is sha256 `5eadbfe0…`, the golden `thesis-auto.docx`. Screenshots 60–107 are the
maintainer's working copy and are not part of the repository.

## Ready-to-use (the default): copy a caption

A new table was added, and the caption of the table above it was copied — the whole paragraph,
with its paragraph mark — pasted under it, and its number typed by hand. After the fields were
updated the list of tables held six entries where it had five, the new one in its place with
its page number. A figure inserted before an existing one, its caption set to `รูปที่ ๒-๑` and
the old one renumbered by hand to `๒-๒`, gave a list of figures of five entries in that order.
The copied caption kept the bold of the one it came from: the copy carries the paragraph's
style, which is what the list in this kind of document collects.

## `--auto-numbering`: Insert Caption, or a copy

**References → Insert Caption** offered the document's own label, `ตารางที่`, and numbered the
new caption `ตารางที่ ๒-๒` — Thai digits, by chapter, after `๒-๑`.

With the lists collecting by style (`TOC \h \z \t "Table Caption,1"`), neither an inserted
caption nor a copied one joined them, though each numbered itself correctly. That was a failed
item of ADR 0012, not a limit: the lists were changed to collect by the counter
(`TOC \h \z \c "ตารางที่"`). On the rebuilt file the list of tables gained the inserted caption,
six entries where there had been five, and the list of figures gained a figure inserted before
an existing one, which renumbered itself from `๒-๑` to `๒-๒`.

## A chapter inserted inside the first chapter's section

The first chapter's section says its page numbers start at 1, and a chapter inserted inside it
gets a copy of that section's settings. The inserted chapter's **Format Page Numbers** showed
**Start at ๑**, and its page read `๑`. Setting it to **Continue from previous section** gave the
page count back its run. A chapter inserted anywhere later needs nothing; this is the answer
`references/numbering.md` gives.

## Not read

- Word for the web: whether it can insert a section break, and whether its Format Painter carries
  a heading's number. The references now say these were not recorded; they are owed with the Word
  for the web reading.
