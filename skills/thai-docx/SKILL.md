---
name: thai-docx
description: Make or check a Word .docx with Thai (ไฟล์ Word ภาษาไทย). When the user's message says "thai-docx grill", use this skill to ask its fixed questions first. https://github.com/sayam/thai-docx-skill
license: MIT (LICENSE.txt)
compatibility: Runs with Python 3.11+ (standard library only) or a JavaScript runtime (Node.js, or a sandbox that runs async JavaScript). No network access or package installs.
metadata:
  author: sayam
  version: "0.2.2"
---

# thai-docx

Word handles Thai as complex script. A .docx written the usual way marks Thai as
Latin text, so Word squiggles every Thai word and breaks lines only at spaces. The
bundled command writes every attribute Thai needs. Your part is the Markdown.

`<skill>` below is the directory that holds this file.

## Rules

- Do not write .docx XML, python-docx, docx.js or any other document code yourself,
  and do not read the scripts' source. The command does all of the formatting.
- Do not add spaces between Thai words, and never add zero-width characters
  (U+200B, U+200C, U+200D, U+2060, U+FEFF). Write Thai as a Thai reader writes it.
- Never change the user's wording or files to get a build through, and never make up what
  they name: a picture that is missing is theirs to give. Tell them the line instead.
- A document with no Thai in it needs nothing this skill adds; build one only if asked to.

## Build a document (default: no questions)

1. **Write the Markdown** to a UTF-8 file, e.g. `report.md` — CommonMark with GitHub's
   tables, strikethrough, task lists and footnotes; local PNG or JPEG images; no HTML
   beyond `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>` and comments. What else stops the build:
   [references/markdown.md](references/markdown.md). A Markdown file the user gave you is
   used as it is. **When the user wants a document of a particular shape** — a letter, a form, a
   report — and shows you one of their own or describes it, read
   [references/specs.md](references/specs.md) first: it is everything the format can express, in
   one page. Match their example, never a form of your own; show the Markdown in the same reply
   as the build, so they can correct it afterwards.
2. **Run the build** with the first runtime you have:

   ```sh
   python3 <skill>/scripts/thai_docx build report.md report.docx
   node <skill>/scripts/thai_docx.js build report.md report.docx
   ```

   Both give the same file, byte for byte, and every command below runs the same with
   `node <skill>/scripts/thai_docx.js` in place of `python3 <skill>/scripts/thai_docx`. With no
   shell: [references/sandbox.md](references/sandbox.md).
3. **Read the one JSON line it prints**, and the exit code — these are `build`'s:

   | exit | JSON | what to do |
   |---|---|---|
   | 0 | `"ok": true` | Done. |
   | 2 | `"error"`, often with `"line"` | Fix what the message names in Markdown you wrote, and run again. In a file the user gave you, tell them the line and what the build takes instead, and change it only as they say. |
   | 1 | `"findings"`, or an `"error"` that says so | A defect in this skill. Nothing was written. Do not retry; tell the user and quote the finding codes. |

   `"warnings"` never stop the build. Pass them on to the user.
4. **Tell the user**, in two or three lines in the language they wrote to you in (not
   necessarily the document's): the file name, the settings used (font, size, paper,
   margins), any warnings, and that any setting can be changed. Give the `sha256` only
   if asked. Read the settings from `"settings"` in the JSON, not from the request: if
   something the user asked for is not there, add its flag and build again.

   > สร้าง `report.docx` แล้ว — ฟอนต์ TH Sarabun New 16 pt, กระดาษ A4, ขอบซ้าย 1.5 นิ้ว
   > ด้านอื่น 1 นิ้ว ปรับค่าใดก็ได้ เช่น ฟอนต์ ขนาด สารบัญ หรือเลขหน้า

Do not ask questions before building — about settings or anything else — unless the
grill command below says to.

## Settings

Defaults: TH Sarabun New 16 pt, A4 portrait, margins 1 in (left 1.5 in), single spacing,
left-aligned, no table of contents or page numbers. Page numbers are `--page-numbers` (top
right), `--page-numbers top-center` or `--page-numbers bottom-center`; heading numbers are
`--heading-numbers`. Every other flag, its default and an example:
[references/settings.md](references/settings.md) — page and type, page furniture, tables,
headings, thesis structure. Read it before you use a flag not named here; never guess a name.

When the user asks for a change ("ขอฟอนต์ Sarabun ขนาด 14", "add page numbers"), build
again with every flag of the last build plus the flags for what they now ask, and report the
new settings; a setting they ask to remove goes back to its default. Add a flag only for what
the user asked for; a setting nobody has mentioned keeps its default. A font without Thai glyphs, or a flag the
document gives nothing to act on, is a warning, not an error.

Heading, list and caption numbers are text the build writes: the same in every application,
but they do not renumber when the .docx is edited. Numbers on headings (1., 1.1, 1.1.1) are
`--heading-numbers`. Only when the user will go on editing in Microsoft Word and wants the numbers
to follow, add `--auto-numbering` as well — and tell them what
[references/numbering.md](references/numbering.md) says other applications draw.

By default the document does not say which complex-script language its Thai is, so Word takes it
from the reader's machine — which every machine that types Thai has (ADR 0038). Add
`--thai-language` when the user says the file goes to a machine that may not, and say in the same
breath that WPS Writer then places ำ over the wrong letter.

A run is marked complex script only where its text is Thai, so English in the file is proofed as
English and code spans take their own font (ADR 0039). When the user says the document is final —
to be read, not edited — and wants one font throughout, English and code included, add
`--force-cs-whole-doc`, and say that Word will then underline correctly spelled English on screen.

**What the file is handed over on is written down once**, in
[references/limits.md](references/limits.md): what the skill promises, what the reader must do
after opening the file, what does not renumber itself once they edit it, where the five
applications differ, and what `repair` will and will not touch. Read it before promising anything
about a file, and pass on the items that apply — a warning the build printed is one of them.

## Grill mode

You do not choose this mode: the script does. Before asking anything, give it everything the
user typed — all of it, word for word and in the language they wrote it in, never translated or
summarised, the argument you were invoked with included, with this skill's name in front of it
as the user typed it, if your client took the name off. The script reads the first 20,000
characters and, when it answers `build`, says in `warnings` if it read fewer than the message
holds; then run it once more with the message's last 20,000 characters, and if that answers
`grill`, that is the answer. Then obey the script's answer:

```sh
python3 <skill>/scripts/thai_docx grill --said 'ช่วยทำไฟล์ word ให้หน่อย'
```

In single quotes, so the shell changes nothing in it (a `'` in the message is written `'\''`).
`"mode": "build"` means build at once, asking nothing. `"mode": "grill"` means ask the
questions the JSON lists, as [references/interview.md](references/interview.md) says — as
choices the user can pick, with your client's question tool if it has one — then run what
its `"next"` says with the args of the chosen choices. An unanswered question keeps its
current choice. Pass on any `"warnings"` in the answer before asking — one says when a `from` or
`save to` later in the message was not read.

## Heading styles

Only when the user asks for a heading look: `heading-1` … `heading-6` lines in the front
matter, with CSS-like declarations —
[references/heading-styles.md](references/heading-styles.md).

## Profiles

A profile is a file of settings the user keeps and shares. Only when they ask for one.

```sh
python3 <skill>/scripts/thai_docx profile save my-thesis --size 15 --align thai
python3 <skill>/scripts/thai_docx build report.md report.docx --profile my-thesis
python3 <skill>/scripts/thai_docx profile export my-thesis my-thesis.json
python3 <skill>/scripts/thai_docx profile import my-thesis.json
```

`profile list` shows the names there are. A flag typed after `--profile` wins. A name is
letters, digits, `-` and `_`. The skill ships one, `thesis` — an example to copy and change,
never a format the user must follow; the document beside it is
[examples/README.md](examples/README.md). A save under a name that hides another says so in its
`"warnings"`: pass it on. Details:
[references/profiles.md](references/profiles.md).

## Chapters, captions and lists

For a report or thesis — cover, front pages, chapters, bibliography, appendices; numbered
table and figure captions; lists of contents, tables and figures. Read
[references/chapters.md](references/chapters.md) and write the Markdown as it shows.

## Check an existing .docx

When the user has a Thai .docx that shows squiggles, odd spacing or bad wrapping:

```sh
python3 <skill>/scripts/thai_docx check file.docx
node <skill>/scripts/thai_docx.js check file.docx
```

Explain each finding by its code, in the user's language:
[references/check.md](references/check.md). `check` exits 1 when the user's file has findings,
and `repair` exits 1 when it wrote the file and findings remain: that is the answer about their
file, not a defect. If the user has the content, rebuilding from Markdown with this skill fixes
everything. If they do not, `repair IN.docx OUT.docx` writes a new file with every finding gone
but a split word, invisible characters and a compatibility mode the file never declared, which it
reports; it says which complex-script font it wrote, and a file with nothing to repair is answered
`ok` with nothing written: [references/repair.md](references/repair.md).

To change a setting of a .docx this skill did not build — its font, page numbers, margins — say
that the skill builds from Markdown: ask for the content, or the Markdown, and build. `repair`
changes the attributes Thai needs and nothing else. Never rewrite the file with document code.
