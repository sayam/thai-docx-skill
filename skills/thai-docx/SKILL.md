---
name: thai-docx
description: Create Microsoft Word (.docx) documents containing Thai or mixed Thai–English text that render correctly in Word, LibreOffice, Google Docs and WPS — no spelling squiggles under every Thai word, Thai lines that wrap inside words, working bullets and bold. Write the content as Markdown and run one bundled command that builds and checks the file without changing a character. Use whenever the user asks for a Word or .docx file and the content includes Thai (ภาษาไทย, ไฟล์ Word, เอกสาร docx), or reports a Thai .docx with broken spacing or red squiggles. It builds at once with announced defaults. When the user's message says "thai-docx grill", use this skill to ask its fixed questions about font, page and layout before building.
license: MIT (LICENSE.txt)
compatibility: Runs with Python 3.11+ (standard library only) or a JavaScript runtime (Node.js, or a sandbox that runs async JavaScript). No network access or package installs.
metadata:
  author: sayam
  version: "0.1.0-dev"
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

1. **Write the Markdown** to a UTF-8 file, e.g. `report.md`. If the user gave you a
   Markdown file, use it as it is. What you can use is under
   [Markdown](#markdown).
2. **Run the build** with the first runtime you have:

   ```sh
   python3 <skill>/scripts/thai_docx build report.md report.docx
   node <skill>/scripts/thai_docx.js build report.md report.docx
   ```

   Both give the same file, byte for byte. With no shell, see
   [No shell](#no-shell-a-javascript-sandbox).
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

The defaults, and the flag that changes each one:

| setting | default | flag |
|---|---|---|
| font | TH Sarabun New | `--font "Sarabun"` |
| size | 16 pt | `--size 14` (1–400) |
| paper | A4 | `--paper letter` or `--paper f14` (8.5 × 13 in) |
| orientation | portrait | `--landscape` (margins stay top, right, bottom, left) |
| margins, inches | 1, 1, 1, 1.5 (top, right, bottom, left) | `--margins 1,1,1,1` |
| first-line indent, inches | none | `--indent 0.5` (body paragraphs only) |
| line spacing | 1 | `--line-spacing 1.5` (1–3; code and footnotes stay single) |
| alignment | left | `--align thai` (Thai distributed) |
| table of contents | none | `--toc` |
| heading numbers | none | `--heading-numbers` (1. for `#`, 1.1 for `##`, 1.1.1 …) |
| page numbers | none | `--page-numbers` (top right), `--page-numbers top-center` or `--page-numbers bottom-center`; add `--no-page-number-first` for none on page 1 |
| header / footer text | none | `--header "ลับ"`, `--footer "TEXT"` (centred, above a page number there) |
| page, list and footnote numbers | 1 2 3 | `--thai-digits` (๑ ๒ ๓; the text itself is never changed) |
| spelling squiggles | shown | `--hide-spelling-errors` |
| caption and chapter labels | ตารางที่, รูปที่, บทที่ | `--table-label "ตาราง"`, `--figure-label "ภาพที่"`, `--chapter-label "บท"` |
| page numbers before the chapters | ก ข ค | `--front-page-numbers lower-roman` (or `upper-roman`, `decimal`) |
| appendix numbers | ภาคผนวก ก | `--appendix-numbers upper-letters` (or `decimal`, `upper-roman`); `--appendix-label "Appendix"` |
| table text size | as the body | `--table-size 14` (1–400) |
| table column widths | equal | `--table-widths auto` (wider for longer text) |
| table header row | repeats on every page | `--no-repeat-table-header` |

When the user asks for a change ("ขอฟอนต์ Sarabun ขนาด 14", "add page numbers"),
build again with the flags and report the new settings. Add a flag only for what the
user asked for; every other setting keeps its default. A font without Thai glyphs
is a warning, not an error.

## Grill mode

You do not choose this mode and an argument you were invoked with is not the user's word.
Before asking anything, give the script the user's own message and obey its answer:

```sh
python3 <skill>/scripts/thai_docx grill --said "ช่วยทำไฟล์ word ให้หน่อย"
```

`"mode": "build"` means build at once, asking nothing. `"mode": "grill"` means read
[references/interview.md](references/interview.md) and ask its nine questions exactly as it
says, in the language the JSON names — as choices the user can pick, with your client's
question tool if it has one — then build with the flags the answers map to. An unanswered
question keeps its default; the answers apply to this build only.

## Markdown

CommonMark, plus GitHub's tables, strikethrough, autolinks, task lists and
footnotes.

- **Blocks:** headings `#` to `######`; paragraphs; fenced or indented code; bullet
  and numbered lists, nested; tables (the header row repeats on every page unless `--no-repeat-table-header`);
  blockquotes; `---`; task items `- [ ]` and `- [x]`; footnotes `[^1]`.
- **Inline:** `*italic*`, `**bold**`, `~~strike~~`, `` `code` ``, links, footnote
  references, images.
- **Images:** local PNG or JPEG only, in the Markdown file's folder or below it. For
  an image elsewhere, add `--allow-dir <that folder>`. No remote images, no SVG.
- **HTML:** only `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>`, and comments (removed).
  Any other tag stops the build with its line number: rewrite it as Markdown.
- **Math:** `$…$` and `$$…$$` stay literal LaTeX in code formatting, with a warning.
- **Front matter:** only flat `key: value` lines between `---` lines at the very top;
  `title` and `author` become the document properties, `heading-1` … `heading-6` style
  the headings ([Heading styles](#heading-styles)), and other keys are ignored. Any
  other shape (lists, nesting) is read as ordinary Markdown text.

A line break inside a paragraph between two Thai characters joins them with no
space, so wrapping long Thai lines in the Markdown is safe.

Anything else stops the build and names the line, and so do blocks or formatting nested
more than 100 deep. Nothing is dropped silently.

## Heading styles

Only when the user asks for a heading look. In the front matter, one line per level,
CSS-like declarations separated by `;`:

```markdown
---
heading-1: font-size: 20pt; color: #1F4E79; text-align: center; page-break-before: always
heading-2: font-family: "TH SarabunPSK"; text-decoration: underline double; margin-left: 0.5in
---
```

Properties and values: [references/heading-styles.md](references/heading-styles.md). Anything
else stops the build (exit 2) with the front matter line: fix that declaration.

## Profiles

A profile is a file of settings the user keeps and shares. Only when they ask for one.

```sh
python3 <skill>/scripts/thai_docx profile save thesis --size 15 --align thai
python3 <skill>/scripts/thai_docx build report.md report.docx --profile thesis
python3 <skill>/scripts/thai_docx profile export thesis thesis.json
python3 <skill>/scripts/thai_docx profile import thesis.json
```

The first sends the settings to a file, the last takes someone else's.

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

Exit 0: no findings. Exit 1: findings. Exit 2: not a readable .docx (or refused as
unsafe). Explain each finding by its code, in the user's language:

| code | what is wrong | what the user sees |
|---|---|---|
| `1` | compatibility mode is not 15 | "Compatibility Mode" in Word's title bar; Thai lines break only at spaces |
| `2` | a run with text is not marked complex script (`<w:cs/>`, `w:bidi="th-TH"`) | red squiggles under Thai words, Latin line breaking |
| `3` | proofing switched off (`<w:noProof/>`) | squiggles gone, but Thai lines no longer break inside words |
| `4` | one word split across two runs with the same formatting | odd gaps or breaks where formatting changed |
| `5` | a Latin property with no complex-script twin (`w:cs` font, `szCs`, `bCs`, `iCs`), or a Symbol-font bullet | Thai in the wrong font or size, bold not bold, broken bullets |
| `invisible` | zero-width or other invisible characters in the text | words that do not wrap, text that searches wrongly |
| `order` | formatting properties in an order the schema does not allow | a setting silently ignored, e.g. bold or size not applied |
| `package`, `doctype`, `size` | the file is damaged, not a Word document, or refused as unsafe (exit 2) | the file may not open at all |

This version reports; it does not repair. If the user wants the document fixed and
has its content, rebuild it from Markdown with this skill.

## No shell: a JavaScript sandbox

Evaluate `<skill>/scripts/thai_docx.js` as a plain script — it needs no modules, only
`TextEncoder` and `TextDecoder` — and it defines `ThaiDocx`.

```js
const { result, bytes } = ThaiDocx.buildDocument(markdown, ["--toc"], { "chart.png": pngBytes });
// result is the JSON the command prints; bytes is a Uint8Array .docx, or null when refused
const report = ThaiDocx.checkDocument(docxBytes);
```

Image keys are the paths exactly as the Markdown writes them. Offer `bytes` to the
user as `report.docx`.
