# Who counts: written numbers, or `--auto-numbering`

A document's numbers — heading numbers (`บทที่ ๑`, `๑.๑`, `ภาคผนวก ก`), ordered-list markers
(`1.` `2.`) and caption numbers (`ตารางที่ ๑-๑`) — are made one of two ways. It is one choice for
the whole document, never a mix. Both work in Arabic digits and with `--thai-digits`.

| | default: written numbers | `--auto-numbering` |
|---|---|---|
| who counts | the build writes each number as text | the application counts: Word's heading numbering, list numbering and caption fields |
| opened in the five applications | **the same in all five** | right in Word; see the table below for the rest |
| the reader inserts a chapter, a heading, a list item or a table | the numbers after it **do not move**: renumber by hand — or change the Markdown and build again, which works every number out afresh | Word renumbers headings and lists at once, and captions when fields are updated (Ctrl+A, then F9) |

Page numbers, footnote marks and the page numbers in a table of contents are the application's
in both: only a laid-out page knows them. The table of contents, list of tables and list of
figures fill in and update in both.

## Which to use

- **Leave the flag off** when the file will be read, printed, handed in or passed on — and when
  you do not know which application will open it. This is most documents. Changing a few words
  in the .docx afterwards is fine; only inserting or removing a *numbered* thing needs care.
- **Use `--auto-numbering`** when the user says they will go on working in **Microsoft Word** —
  adding chapters, moving sections, inserting tables — and wants the numbers to follow. Say, when
  you hand the file over, that it is made for Word and what the table below says about the
  application they named, if they named another.

When the user has not said, leave it off, and mention in one line that `--auto-numbering` exists
for a document they will keep editing in Word.

## What each application draws with `--auto-numbering`

Only what has been measured is here. A blank is not a promise.

| application | Arabic digits | with `--thai-digits` | chapter-numbered captions (region comments) |
|---|---|---|---|
| Word 365 for Windows | correct; a heading, chapter, list item or caption inserted renumbers what follows | correct, in Thai digits | correct |
| Word on the web | headings and lists as the desktop; **no section break can be inserted** (Layout → Breaks offers Page and Column only), and Format Painter does not carry a heading's number — apply the Heading style instead | correct, in Thai digits | correct |
| Word for macOS | correct | headings correct (`บทที่ ๑`, `๑.๑`), at the heading's size | not measured on its own |
| Google Docs | correct as opened; renumbering on edit not measured | not measured | correct as opened |
| LibreOffice Writer | correct | **draws 1, 2, 3** — it has no Thai-digit numbering | **wrong**: `ตารางที่ บทนำ-ก` — it answers the chapter-number field with the chapter's *title*, and ignores the restart at each chapter |
| WPS Writer | list numbers correct; **a Thai chapter label is drawn as Latin letters** (`ÓõõõyA 1` for `บทที่ 1`) | **the value 1 is drawn as ๕** (2 and 3 are right) | not measured |

These are those applications' own behaviour on the numbering the file asks for; no attribute in
the file changes them. Until an application is updated, the way to have it draw the numbers right
is to leave `--auto-numbering` off.

## Inserting a caption yourself, in Word

`--auto-numbering` writes the document's caption labels into the file, so **References → Insert
Caption** already offers `ตารางที่` and `รูปที่` (or whatever `--table-label` and `--figure-label`
say), already set to the document's number format, to number by chapter, and to sit above a table
and below a figure. The counter is the document's own, so a caption inserted between two others
takes the next number and the ones after it move on when fields are updated (Ctrl+A, then F9).

A label carrying a space is not one Word's `SEQ` field can name; keep a caption label to one word.

## What written numbers cost

Nothing renumbers itself. After inserting a chapter in the .docx, every later `บทที่`, every
`๒.๑` under it and every `ตารางที่ ๒-๑` is renumbered by hand — or, better, the change is made in
the Markdown and the document built again. The three lists still update from the text that is
there, so a caption renumbered by hand appears correctly in its list after fields are updated.

## The flag that did nothing

In a document with no numbered heading, no ordered list and no caption there is nothing to count:
`--auto-numbering` changes no byte, and the build's warning says so. Pass the warning on.
