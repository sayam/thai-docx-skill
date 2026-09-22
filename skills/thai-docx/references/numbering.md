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

**One kind or the other, never both.** A document that numbers itself is the second kind
throughout. Mixing the two is not offered in this version or the next few: a document that
renumbers its headings but not its captions goes wrong in silence, and carrying both would cost
more of the package than a skill should.

**Every other setting works in both.** The paragraph layout, the indents, Thai distributed
alignment, line spacing, heading styles, chapter and appendix labels, caption labels, table
widths and page numbering are the same either way — including `--indent`,
`--caption-hanging-indent`, `--caption-matches-object` and `--center-images`. Only the numbering
differs.

## What each application draws with `--auto-numbering`

Only what has been measured is here. A blank is not a promise.

**Only Word 365 for Windows, on the desktop, is held to this.** A document built with
`--auto-numbering` is made for editing there; everything below is recorded, not promised.

| application | Arabic digits | with `--thai-digits` | chapter-numbered captions (region comments) |
|---|---|---|---|
| **Word 365 for Windows** (the one this mode is for) | correct; a heading, chapter, list item or caption inserted renumbers what follows | correct, in Thai digits | correct |
| Word on the web | numbers as the desktop does, but **not covered for this mode**: no section break can be inserted at all (Layout → Breaks offers Page and Column only), and Format Painter does not carry a heading's number — apply the Heading style instead. A document to be edited there is a ready-to-use one | correct, in Thai digits | correct |
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

The list of tables and the list of figures gain it. Under this flag they collect the document's
counter rather than the caption's style, so a caption joins them whichever way it was added and
whatever style it ended up in — Insert Caption, or a copy of one already there. Update the fields
and it is listed; a figure inserted before another renumbers the one that follows it, in the
document and in the list alike.

## Adding a caption yourself where the build writes the numbers

Insert Caption is for `--auto-numbering`: it asks Word to count, and in a ready-to-use document
the numbers are text, so it would start a second count of its own beside them. The route that
suits this kind of document is a copy:

1. Add the table or the figure.
2. **Select a caption that is already there, the whole paragraph including its paragraph mark**,
   and copy it. Clicking once in the left margin beside the line selects exactly that.
3. Paste it where the new caption goes, and **type the new number by hand**. Renumber the
   captions after it yourself, if there are any.
4. Update the fields (Ctrl+A, then F9), choosing **Update entire table** when Word asks.

The list of tables or of figures gains it. What makes this work is the copy carrying the
caption's style, which is what these lists collect; selecting only the words and pasting them
into an empty paragraph leaves the style behind and the list will not see it. If that happens,
click in the pasted caption and set its style to **Table Caption** or **Figure Caption** by hand,
then update the fields again.

## A caption that runs to a second line

By default every line of a caption starts at the margin, so a caption that runs on continues under
its own number. `--caption-hanging-indent 0.75` (inches, 0 to 4) keeps the label and number at the
margin and indents every line after the first, which puts the caption's text in one block beside
its number. It is its own setting: `--indent` is the first line of a body paragraph and changes no
caption, and a caption is not indented until this flag asks for it.

A figure's caption is centred, so the indent there moves the block in from the left and each line
is centred in what is left; a table's caption is left-aligned and hangs as the flag describes.

## A caption as wide as the picture it belongs to

By default a caption fills the width of the text, whatever the size of the picture above it, so a
caption under a small picture runs on past both its edges. `--caption-matches-object` indents a
figure's caption to the picture's own box: the caption then starts and ends where the picture
does. `--center-images` centres a picture that stands alone on its line, and the caption's box is
centred with it; without it the picture keeps the left margin and all the indent goes on the right.
Each flag works on its own, and both are off unless asked for.

A table is written at the full width of the text, so its caption is already as wide as it is and
neither flag moves it. A picture wider than the text is drawn at the text width, so there is
nothing to indent.

## What written numbers cost

Nothing renumbers itself. After inserting a chapter in the .docx, every later `บทที่`, every
`๒.๑` under it and every `ตารางที่ ๒-๑` is renumbered by hand — or, better, the change is made in
the Markdown and the document built again. The three lists still update from the text that is
there, so a caption renumbered by hand appears correctly in its list after fields are updated.

## The flag that did nothing

In a document with no numbered heading, no ordered list and no caption there is nothing to count:
`--auto-numbering` changes no byte, and the build's warning says so. Pass the warning on.
