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
Writer, Google Docs and WPS Writer before every release that changes a document's bytes. v0.2.0
went out with Word for macOS not yet read on its bytes and LibreOffice Writer read on the
`--auto-numbering` document only; both readings are owed
(record: `docs/evidence/2026-09-24-what-v0.2.0-was-read-in.md` in the repository).
**Nothing outside those five applications is covered**, and it must never be described as working.

**`--auto-numbering` is held to Word on the desktop, and to nothing else.** Word on the web is not
covered for it, so a document meant to be edited there is a ready-to-use one. (That the web
version cannot insert a section break, and that its Format Painter does not carry a heading's
number, was seen but never recorded; it is owed with the Word for the web reading.) What the other
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
- **Never ask Google Docs to update the lists.** It has no list of tables and no list of figures of
  its own, so an update rewrites **all three** as a table of contents built from headings: the
  list of tables and the list of figures lose their entries and repeat the contents instead
  (measured 2026-09-20). Read them there as they came — the entries are already in the file — and
  update in Word, LibreOffice or WPS. Nothing the file could say differently reaches this, and the
  way back is to download the document again.
- **Have Thai among the machine's languages, or build with `--thai-language`.** By default the
  document does not say which complex-script language its Thai is (ADR 0038), so Word uses the
  machine's own. Every machine that types Thai has it, and nothing is underlined. On a machine
  that does not — a colleague abroad, a shared machine, a server that renders documents — Word
  underlines every correctly spelled Thai word. Building again with `--thai-language` writes the
  language into the document and settles it in Word. **The cost is WPS Writer**: in a document
  built with that flag it places SARA AM (ำ) over the wrong letter. **LibreOffice Writer does not
  read the machine's languages**: it takes its own default for complex text layout (Tools →
  Options → Languages and Locales → General), which on an English installation is Hindi, and
  underlines every Thai word until that is set to Thai (measured 2026-09-23 on an
  `--auto-numbering` document; expected of every document built without `--thai-language`, not yet
  measured on one). Whether
  `--thai-language` settles it there has not been measured.
- **Install the font the file names.** The default is TH Sarabun New; a file names whatever
  `--font` said. A font that is not on the reader's machine is outside the rendering contract —
  the application substitutes, and the page will not look the same. Sarabun is free from Google
  Fonts.
- **For a document to be read or edited in Word for the web, build with
  `--font "TH SarabunPSK"`.** That application's font list has no TH Sarabun New. Asked for a font
  it does not have it substitutes one whose mark metrics are not the font's, and the tone marks
  float above the letter (ป้า ม้า ค้า ค่า) throughout the document — including text typed in by
  hand afterwards. TH SarabunPSK is in its list and draws them in place (measured 2026-09-20).
  The default stays TH Sarabun New, which Word on the desktop, LibreOffice and WPS all have.
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
  repair changes attributes only — see §10. Do not offer it.

## 5. What the reader adds to the document, in either kind

**What they type into a paragraph the build wrote takes that paragraph's font**, Thai and Latin
alike: every style the package carries names its fonts outright.

**What Word itself makes takes the document's font too** — a table inserted from the ribbon, the
`Caption` style Word creates the first time a caption is inserted. The package carries a theme
naming the document's font as the document's own, so Word resolves its `+Body` and `+Headings`
against this document rather than against its own Office theme. Without it the Latin letters in
anything Word added came out in Word's default face, and the font box showed no name at all.

The theme names one font for Latin, complex-script and East Asian text: whatever `--font` said.
A document built with a font that carries no Thai still warns, as it always did.

## 6. What never renumbers or updates itself, in either kind of document

- **Page numbers, footnote marks, and the page numbers inside the three lists** are always the
  application's: only a laid-out page knows them.
- **The entries of the three lists are written into the file** so they show in an application that
  never updates fields — but they carry no page numbers and no links until an update.
- **An ordered list starts at the number the Markdown typed.** Nothing recounts it.
- **`--auto-numbering` is one answer for the whole document**, never a mix.
- **A caption the reader adds joins the lists in both kinds of document — by a different route
  in each.** Measured in Word 365 for Windows on 2026-09-23
  (record: `docs/evidence/2026-09-23-editing-in-word-after-the-build.md` in the repository).

  **Ready-to-use (the default).** Add the table or figure, then **copy a caption that is already
  there — the whole paragraph, including its paragraph mark — paste it, and type the new number
  by hand**. Update the fields and it appears in the list of tables or figures. The copy is what
  carries the caption's style, which is what the list collects; selecting only the words and
  pasting them into an empty paragraph leaves the style behind, and the list will not see it.
  Do not use References → Insert Caption here: it asks Word to count, and in this kind of
  document the numbers are text, so it would start a second count of its own beside them.

  **`--auto-numbering`.** Either route works — Insert Caption or a copy — and the number counts
  itself. Insert Caption already offers this document's labels, in its digits, numbered by
  chapter. A figure inserted before another renumbers the one that follows it.

  In both kinds, a caption long enough to fill the line wraps in the list, and its page number
  sits on the second line. That is the application laying out a long line, and no attribute
  reaches it.
- A flag that reaches nothing in the document changes no byte, and — except `--heading-numbers` in
  a document without headings — the build says which flag and what was missing. Pass that on.
  `--thai-language` in a document with no Thai text still names the language in the styles, and
  the build says it reached no run.

## 7. Where the five applications differ, as measured

Each of these is a difference of that application, on a file that is correct in the reference
application. None can be reached by anything the file could say differently.

| application | what it draws its own way |
|---|---|
| **WPS Writer** | **with `--thai-language`, SARA AM (ำ) placed over the wrong letter** — it is that flag's `w:bidi="th-TH"` that WPS trips over, measured attribute by attribute on 2026-09-20 and again on 2026-09-23, and a ำ under a tone mark (น้ำ) is drawn correctly; the three lists show no page numbers until References → Update (§3). A chapter label drawn as Latin letters (`ÓõõõyA 1`) and the value 1 drawn as ๕, recorded on 2026-09-19, did not reproduce on 2026-09-23 — on a build from before ADR 0039 as well as the current one — and what changed is not established |
| **LibreOffice Writer** | with `--auto-numbering`: Thai-digit numbering drawn as 1, 2, 3, and a chapter-numbered caption as `ตารางที่ บทนำ-ก` — it answers the chapter-number field with the chapter's *title*, ignores the restart at each chapter and draws the Thai-digit counter as Thai letters (ก, ข, ค). A chapter-numbered caption LibreOffice makes itself loses its chapter number the same way once saved as .docx, opened again and updated (measured 2026-09-24) |
| **Google Docs** | converts a table of contents into an object of its own, with its own font and page numbers; **has no list of tables and no list of figures**, so asking it to update rewrites all three as heading lists and the two lose their entries (§3 — do not ask it to update) |
| **Word on the web** | **has no TH Sarabun New in its font list** (TH SarabunPSK is there), and the font it substitutes floats the tone marks above the letter (§3 — build with `--font "TH SarabunPSK"` for that destination); cannot insert a section break (Layout → Breaks offers Page and Column only); Format Painter does not carry a heading's number — apply the Heading style instead |
| **Word for macOS** | correct in what was measured, on the bytes before 0.2.0 (not yet read on 0.2.0's); a heading's number takes its heading's size |

Two more that are not any application's fault:

- **Word does not repair a Thai file it did not type.** Opening and saving another program's file
  rewrites the runs, stamps them `en-US`, and still writes no complex-script mark. An assistant
  working inside Word does the same.
- **A difference may change when the other side updates.** Every one here is re-measured whenever
  a document's bytes change, and CI passing is a proxy — not the applications passing.

## 8. What changed with 0.2.0 that a reader will notice

**Code is drawn in the monospace font the document names for it.** Every release before 0.2.0
marked every run as complex script, and that marking tells an application to take the font from
the complex-script slot — so a code span and a code block were drawn in the body font, not in the
monospace one the build had asked for all along. Now that only complex-script runs are marked, the
font the run names is the one used. Measured in Word 365 for Windows and in Google Docs on
2026-09-23; both draw `Consolas`.

**An application draws its own red underline under code**, because `w:ascii` and `w:szCs` are not
words in any language. Word does; Google Docs does not. The underline does not print, and
`--hide-spelling-errors` hides it on screen.

**`--force-cs-whole-doc` gives one font throughout in Word, and all but the code blocks in Google
Docs.** The flag marks every run complex script, so an application takes the font from the
complex-script slot and code is drawn in the body font again. Word does this for a code span and
for a code block alike. **Google Docs does it for a code span only**: a code span carries its own
`w:rFonts` and that application honours the complex-script slot there, while a code block takes
its font from the `CodeBlock` style, where the slot is ignored — so code blocks stay monospace
there. Measured in both on 2026-09-23. The flag brings the underlines back with it, everywhere the
document has English; that is the exchange it exists to offer, and it is why it is not the
default.

**What did not change: the number of words an application counts.** A run no longer repeats the
language the document already declares, which could have changed how Word segments text for its
count, and one file made by hand during the investigation did count differently. **It did not
happen to the files this project builds**: the thesis fixture counts 3,177 words in Word 365 for
Windows on 2026-09-23, exactly as it did before. This is written down because the earlier figure
was published here in error.

## 9. What the build refuses, and what it only warns about

**Refused — no file is written, and the line is named:** any HTML but `<br> <sup> <sub> <u>
<kbd>` — and one of those alone on its own line, which is an HTML block; a character a reader
cannot see — a zero-width character, a soft hyphen, a direction mark or any other format
character, or a noncharacter; a link to anything but `http`, `https` or `mailto` (a link with no
scheme, `#top` or `other.docx`, is written as before); nesting past 100 deep; a footnote defined and never
referenced, or defined twice; an image that is not PNG or JPEG by its bytes, is truncated, is
remote (a URL; a drive path such as `C:\…` is a path, and read as one), is wider or taller than
20,000 pixels, is larger than 32 MiB, or lies outside the
Markdown's own directory unless `--allow-dir` names one — through at most 40 symbolic links; a table row
with more cells than its header; region comments out of order or twice; a front-matter or flag
value outside its range; a caption label holding `%`, `"` or `\`, or a table or figure label
holding a space under `--auto-numbering` (Word's counter takes one word); margins, an indent or a
caption's hanging indent that leave less than an inch for text; and any difference at all between
the text written and the Markdown.

**Refused before anything is read:** a Markdown file larger than 16 MiB, or one that is not a
regular file (a FIFO, a device); an output path that is the Markdown file itself; an argument that
is not UTF-8 text.

**A picture is fitted to the page** — to the text width, and to the text height too, so a tall
one no longer runs off the page.

**Warned — the file is written, and the warning must be passed to the user:** a flag that changed
nothing; `--toc` beside `<!-- toc -->`, which gives two tables of contents; a font not known to
carry Thai; `![]` with nothing between the brackets; a heading level skipped; a link definition
nobody refers to; `ำ` typed the long way (`ํ` + `า`), which is left exactly as typed and which a
search for `ำ` will not find; a `Table:` or `Figure:` line in a place where it is not a caption;
a Thai caption prefix, which is not one — the prefix is `Table:`/`Figure:` in every language;
a region comment inside a list, quotation or footnote; `$…$` math kept as literal LaTeX.

**`build` overwrites the output path without asking** — any path but the Markdown's own. Give a
new name to keep the old file.

**Exit 1 with `findings`, or with an `error` that says so, means a defect in this skill**: nothing
was written, do not retry, quote the codes.

## 10. What `repair` does, and what it never does

`repair` is for a Word file the user has and cannot rebuild from Markdown.

**It does:** set a declared compatibility mode to 15 (a file that declares none is left so); **mark a run as complex script where its text is complex
script, and take the marker off where it is not** — off the document defaults and the styles too,
without which a run that leaves it off only inherits it again; **cut a run that holds both scripts
where the script changes**, so the English inside a Thai sentence stops being proofed with a
complex-script dictionary; remove `noProof`; write the missing twin of a size, bold or italic;
give a run that names only a Latin font a complex-script one; give a Symbol bullet a font with Thai
in it; put properties back into schema order. `--force-cs-whole-doc` marks every run instead and cuts nothing, which is the shape
releases before 0.2.0 wrote.

**It never:** changes a character of the text — the output's text, in every part a reader sees, is
compared with the input's, and a one-character difference writes nothing — nor writes a file its
own checker faults where the input was sound (a defect: exit 1); cuts a run inside a word at an
invisible character, or where a space at its ends lacks `xml:space="preserve"`; edits a part that
holds an XML comment, CDATA or a processing instruction (left as it came, with a warning); repairs
a document written under a prefix other than `w:` (refused); **cuts a run that carries anything but its own text** —
a field, a picture, a tab, a line break, or a numeric character reference such as `&#x20;`, which
could not be written again without changing the text, so each of those keeps its whole run and the
English inside it keeps its underline; merges a word split across two runs (reported, left);
removes an invisible character (reported, left); touches fonts, styles, layout, tracked changes,
fields or document properties beyond the list above; or overwrites the original — a new file is
written, always, both paths are given to the user, and an output that is the input — by its
path, a link or a hard link — is refused. A file with nothing to repair is answered `ok`, with
nothing written.

**What follows from it:** compatibility mode 15 **reflows the document, and page breaks can move**
— say so before the user sends the file to anyone. The complex-script font it writes where a run
names none is a decision it made: it is in `warnings`, so read it out. `repair` promises nothing
about the layout of a document somebody else made; it is measured only by its own contract.
**Rebuilding from Markdown is better whenever the content exists.**

## 11. What this skill is not

- **It carries no institution's form.** The `thesis` profile and `examples/thesis.md` are an
  example to copy, not a standard, and every word and number in them is invented. The skill will
  never ship a real ministry's, university's or company's template.
- **It does not lay out somebody else's document, or typeset one.** What the application does, the
  application does.
- **A document with no Thai in it needs nothing this skill adds.**
- **Reading a PDF or a photograph of an example is the assistant's ability, not the skill's.**
- **It never reaches the network, installs nothing, and reads only the Markdown's own directory
  tree (or an `--allow-dir`, never `/` or an empty one) and the profile locations** — only regular
  files, each to a ceiling — writing only the output path and the one profile file it was asked to
  save, that one whole or not at all.
- **The two implementations give the same bytes when their runtimes share a Unicode version.**
  Whether `_` or `*` opens emphasis, and how a link label's case is folded, are read from the
  runtime's own Unicode tables; a character newer than one runtime's tables can read differently
  in the other. The characters the skill refuses are one list both read, whatever the
  version.
