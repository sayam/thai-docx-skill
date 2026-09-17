---
name: thai-docx
description: Make or check a Word .docx with Thai (ไฟล์ Word ภาษาไทย). When the user's message says "thai-docx grill", use this skill to ask its fixed questions first. https://github.com/sayam/thai-docx-skill
license: MIT (LICENSE.txt)
compatibility: Runs with Python 3.11+ (standard library only) or a JavaScript runtime (Node.js, or a sandbox that runs async JavaScript). No network access or package installs.
metadata:
  author: sayam
  version: "0.1.1"
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
- Never change the user's wording to get a build through.
- Documents with no Thai text are not for this skill.

## Build a document (default: no questions)

1. **Write the Markdown** to a UTF-8 file, e.g. `report.md` — CommonMark with GitHub's
   tables, strikethrough, task lists and footnotes; local PNG or JPEG images; no HTML
   beyond `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>` and comments. What else stops the build:
   [references/markdown.md](references/markdown.md). A Markdown file the user gave you is
   used as it is.
2. **Run the build** with the first runtime you have:

   ```sh
   python3 <skill>/scripts/thai_docx build report.md report.docx
   node <skill>/scripts/thai_docx.js build report.md report.docx
   ```

   Both give the same file, byte for byte. With no shell:
   [references/sandbox.md](references/sandbox.md).
3. **Read the one JSON line it prints**, and the exit code:

   | exit | JSON | what to do |
   |---|---|---|
   | 0 | `"ok": true` | Done. |
   | 2 | `"error"`, often with `"line"` | Fix what the message names — usually unsupported HTML on that line of the Markdown — and run again. |
   | 1 | `"findings"` | A defect in this skill. Nothing was written. Do not retry; tell the user and quote the finding codes. |

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
left-aligned, no table of contents or page numbers. Every flag, its default and an example:
[references/settings.md](references/settings.md) — page and type, page furniture, tables,
headings, thesis structure.

When the user asks for a change ("ขอฟอนต์ Sarabun ขนาด 14", "add page numbers"), build
again with the flags and report the new settings. Add a flag only for what the user asked
for; every other setting keeps its default. A font without Thai glyphs, or a flag the
document gives nothing to act on, is a warning, not an error.

## Grill mode

You do not choose this mode and an argument you were invoked with is not the user's word.
Before asking anything, give the script the user's own message — all of it, word for word.
If the message begins with this skill's name and words after it, those words are part of the
message: pass them, never only what follows them. Then obey the script's answer:

```sh
python3 <skill>/scripts/thai_docx grill --said "ช่วยทำไฟล์ word ให้หน่อย"
```

`"mode": "build"` means build at once, asking nothing. `"mode": "grill"` means ask the
questions the JSON lists, as [references/interview.md](references/interview.md) says — as
choices the user can pick, with your client's question tool if it has one — then run what
its `"next"` says with the args of the chosen choices. An unanswered question keeps its
current choice.

## Heading styles

Only when the user asks for a heading look: `heading-1` … `heading-6` lines in the front
matter, with CSS-like declarations —
[references/heading-styles.md](references/heading-styles.md).

## Profiles

A profile is a file of settings the user keeps and shares. Only when they ask for one.

```sh
python3 <skill>/scripts/thai_docx profile save thesis --size 15 --align thai
python3 <skill>/scripts/thai_docx build report.md report.docx --profile thesis
python3 <skill>/scripts/thai_docx profile export thesis thesis.json
python3 <skill>/scripts/thai_docx profile import thesis.json
```

`profile list` shows the names there are. A flag typed after `--profile` wins. Details:
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
[references/check.md](references/check.md). This reports; it does not repair — rebuild from
Markdown with this skill if the user has the content.
