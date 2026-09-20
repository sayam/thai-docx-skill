# What this skill does, what it does not, and what follows

The terms the document is handed over on. Read this before promising anything about a file the
skill built, and tell the user the items that apply to what they asked for — in their own language.
Nothing here is a surprise to be found later; every line is measured or refused, never assumed.

## 1. The one promise

**The text of the document is the user's Markdown, character for character.** Not a space is added
between Thai words, not an invisible character is inserted, nothing is re-worded to make a page
look better. Where the skill cannot do that, it writes no file and says which line stopped it
(ADR 0023).

Everything the skill adds around that text — a heading's number, a caption's label and number, a
list marker, the entries of a table of contents — is **generated matter**. It belongs to the
build, and the build is the only thing that changes it.

## 2. Two kinds of document, and the contract each is held to

| | default — **ready to use** | `--auto-numbering` — **made for editing in Word** |
|---|---|---|
| for | a document to be read, printed, handed in or passed on, with small edits | a document a Word user will go on working on |
| who counts the numbers | the build writes them as text | Word counts, and renumbers as the user edits |
| held to | **the five applications** | **Word 365 for Windows, on the desktop — that alone** |
| a reader edits it | the numbers do not move; the reader keeps the format (§4) | Word's own numbering, captions and styles carry on working |

**The five-application contract covers the ready-to-use document.** It is opened in Word 365 for
Windows (the reference application, which must pass every item), Word for macOS, LibreOffice
Writer, Google Docs and WPS Writer before every release that changes a document's bytes.
**Nothing outside those five applications is covered**, and it must never be described as working.

**`--auto-numbering` is held to Word on the desktop, and to nothing else.** Word on the web is not
covered for it — it cannot insert a section break at all, and its Format Painter does not carry a
heading's number — so a document meant to be edited there is a ready-to-use one. What the other
applications draw with `--auto-numbering` is recorded in [numbering.md](numbering.md), each line
measured; a blank there is not a promise.

**A document is one kind or the other, never both.** The moment a document numbers itself, it is
the second kind: a document that renumbers its headings but not its captions goes wrong in silence
the first time a chapter is inserted. Mixing them is not offered in this version or the next few —
it would cost more of the package than a skill should.

**What the second kind is for.** It carries everything the ready-to-use document does — the
paragraph layout, the left and right indents, Thai distributed alignment, line and paragraph
spacing, the heading styles the front matter sets, the chapter and appendix labels, the caption
labels and their number format, the table widths, the page numbering of each region — and adds the
numbering on top, so that a Word user can go on with Word's own tools: heading numbering that
follows what they type, References → Insert Caption offering this document's labels, the three
lists updating from what is there. Every setting works in both kinds; only the numbering differs.

## 3. What the reader must do after opening the file

- **Update the fields to get page numbers in the three lists.** The table of contents, list of
  tables and list of figures show their entries the moment the file opens — the build writes them
  in — but the page numbers beside them are the application's, and appear only after an update.
  Word on the desktop offers to do it on open; elsewhere it is manual: **Word** Ctrl+A then F9 ·
  **LibreOffice** Ctrl+Shift+F9 · **WPS** References → Update.
- **Install the font the file names.** The default is TH Sarabun New; a file names whatever
  `--font` said. A font that is not on the reader's machine is outside the rendering contract —
  the application substitutes, and the page will not look the same. Sarabun is free from Google
  Fonts.
- **Keep the file.** In a chat app, download the .docx and keep any profile `.json`: chat apps
  forget files when the chat ends.
- With `--auto-numbering`, **caption numbers move only after an update** (Ctrl+A, then F9);
  heading and list numbers move as you type.

## 4. If the reader edits a ready-to-use document (the default)

**The format is theirs from that moment.** The skill has handed over a document whose numbers are
text; it does not watch it afterwards.

- **Nothing renumbers.** Insert a chapter, a heading, a list item, a table or a figure and every
  number after it stays as it was. Renumber by hand from there.
- **A new paragraph carries the formatting of wherever it was typed**, not the pattern of its
  neighbours: its indent, its font and its size may differ from the rest.
- **A caption renumbered by hand still lists correctly** once fields are updated — the lists
  collect the caption's paragraph style, not its number.
- **The way back is to change the Markdown and build again**, where every number is worked out
  afresh. That is what the skill is for, and it is the answer whenever the Markdown still exists.
- **Bringing the edited file back to `repair`** so that it re-runs the numbers and brings a
  paragraph into line with its neighbours is decided (ADR 0037) and **not yet shipped**. Today
  repair changes attributes only — see §8. Do not offer it.

## 5. What never renumbers or updates itself, in either kind of document

- **Page numbers, footnote marks, and the page numbers inside the three lists** are always the
  application's: only a laid-out page knows them.
- **The entries of the three lists are written into the file** so they show in an application that
  never updates fields — but they carry no page numbers and no links until an update.
- **An ordered list starts at the number the Markdown typed.** Nothing recounts it.
- **`--auto-numbering` is one answer for the whole document**, never a mix.
- A flag that reaches nothing in the document changes no byte, and the build says which flag and
  what was missing. Pass that on.

## 6. Where the five applications differ, as measured

Each of these is a difference of that application, on a file that is correct in the reference
application. None can be reached by anything the file could say differently.

| application | what it draws its own way |
|---|---|
| **WPS Writer** | a Thai label in a numbering level through a legacy code page — `บทที่ 1` reads `ÓõõõyA 1`; SARA AM (ำ) placed over the wrong consonant, in every weight and font tried; with `--auto-numbering --thai-digits` the value 1 drawn as ๕ (2 and 3 are right) |
| **LibreOffice Writer** | with `--auto-numbering`: Thai-digit numbering drawn as 1, 2, 3, and a chapter-numbered caption as `ตารางที่ บทนำ-ก` — it answers the chapter-number field with the chapter's *title* and ignores the restart at each chapter |
| **Google Docs** | converts a table of contents into an object of its own, with its own font and page numbers |
| **Word on the web** | cannot insert a section break (Layout → Breaks offers Page and Column only); Format Painter does not carry a heading's number — apply the Heading style instead |
| **Word for macOS** | correct in what was measured; a heading's number takes its heading's size |

Two more that are not any application's fault:

- **Word does not repair a Thai file it did not type.** Opening and saving another program's file
  rewrites the runs, stamps them `en-US`, and still writes no complex-script mark. An assistant
  working inside Word does the same.
- **A difference may change when the other side updates.** Every one here is re-measured whenever
  a document's bytes change, and CI passing is a proxy — not the applications passing.

## 7. What the build refuses, and what it only warns about

**Refused — no file is written, and the line is named:** any HTML but `<br> <sup> <sub> <u>
<kbd>`; invisible characters in the text; nesting past 100 deep; a footnote defined and never
referenced, or defined twice; an image that is not PNG or JPEG by its bytes, is truncated, is
remote, or lies outside the Markdown's own directory unless `--allow-dir` names one; a table row
whose cells do not match its header; region comments out of order or twice; a front-matter or flag
value outside its range; margins or an indent that leave less than an inch for text; and any
difference at all between the text written and the Markdown.

**Warned — the file is written, and the warning must be passed to the user:** a flag that changed
nothing; `--toc` beside `<!-- toc -->`, which gives two tables of contents; a font not known to
carry Thai; `![]` with nothing between the brackets; a heading level skipped; a link definition
nobody refers to; `ำ` typed the long way (`ํ` + `า`), which is left exactly as typed and which a
search for `ำ` will not find; a `Table:` or `Figure:` line in a place where it is not a caption;
a Thai caption prefix, which is not one — the prefix is `Table:`/`Figure:` in every language;
a region comment inside a list, quotation or footnote; `$…$` math kept as literal LaTeX.

**`build` overwrites the output path without asking.** Give a new name to keep the old file.

**Exit 1 with `findings` means a defect in this skill**: nothing was written, do not retry, quote
the codes.

## 8. What `repair` does, and what it never does

`repair` is for a Word file the user has and cannot rebuild from Markdown.

**It does:** set compatibility mode 15; mark every run with text as complex-script Thai; remove
`noProof`; write the missing twin of a size, bold or italic; give a run that names only a Latin
font a complex-script one; put properties back into schema order.

**It never:** changes a character of the text — the output's text is compared with the input's and
a one-character difference writes nothing; merges a word split across two runs (reported, left);
removes an invisible character (reported, left); touches fonts, styles, layout, tracked changes,
fields or document properties beyond the list above; or overwrites the original — a new file is
written, always, and both paths are given to the user.

**What follows from it:** compatibility mode 15 **reflows the document, and page breaks can move**
— say so before the user sends the file to anyone. The complex-script font it writes where a run
names none is a decision it made: it is in `warnings`, so read it out. `repair` promises nothing
about the layout of a document somebody else made; it is measured only by its own contract.
**Rebuilding from Markdown is better whenever the content exists.**

## 9. What this skill is not

- **It carries no institution's form.** The `thesis` profile and `examples/thesis.md` are an
  example to copy, not a standard, and every word and number in them is invented. The skill will
  never ship a real ministry's, university's or company's template.
- **It does not lay out somebody else's document, or typeset one.** What the application does, the
  application does.
- **A document with no Thai in it needs nothing this skill adds.**
- **Reading a PDF or a photograph of an example is the assistant's ability, not the skill's.**
- **It never reaches the network, installs nothing, and reads only the Markdown's own directory
  tree (or an `--allow-dir`) and the profile locations** — writing only the output path and the one
  profile file it was asked to save.
