# Chapters, captions and lists

Read this for a report or thesis (SKILL.md, Chapters, captions and lists). Without the
region comments below, a document builds as a plain one: no sections, no chapter numbers.

## The Markdown

Mark the parts with comments, each alone on its line with blank lines around it; what
comes before the first is the cover:

```markdown
**ชื่อรายงาน**

<!-- front -->

# สารบัญ

<!-- toc -->

# สารบัญตาราง

<!-- list-of-tables -->

<!-- chapters -->

# บทนำ

Table: ผลการสำรวจ

| ด้าน | คะแนน |
|---|--:|
| บริการ | 4.5 |

![แผนภูมิผลการสำรวจ](chart.png)

Figure: ขั้นตอนการทำงาน

<!-- back -->

# บรรณานุกรม

<!-- appendices -->

# แบบสอบถาม

Table: ผู้ตอบแบบสอบถาม

| เพศ | จำนวน |
|---|--:|
| หญิง | 12 |

<!-- back -->

# ประวัติผู้เขียน
```

## The rules

- **Regions:** `front`, `chapters`, `back`, `appendices`, then `back` again, in that order,
  each once; any may be left out. Out of order stops the build with the line. Write the
  comments exactly so, in lower case, never inside a list or quotation — a warning names
  any that is read as an ordinary comment.
- **Pages:** every `#` starts a new page (a section). The cover has no page number; front
  pages count ก ข ค; the chapters restart at 1 and the rest go on from there. Page numbers
  show only when the build is given them (below).
- **Chapters:** in `chapters`, `#` reads "บทที่ 1 บทนำ" — the comment alone does this; a
  request for "บทที่ 1" or numbered chapters needs no flag.
- **Appendices:** in `appendices`, `#` reads "ภาคผนวก ก แบบสอบถาม". Headings in the cover,
  `front` and `back` have no number.
- **Captions:** `Table:` just before a table and `Figure:` just after an image alone in its
  paragraph become "ตารางที่ 1-1 …" and "รูปที่ 1-1 …" in a chapter, "ตารางที่ ก-1 …" in
  an appendix, "ตารางที่ 1 …" elsewhere or with no region comments. Leave a blank line
  between a caption and its image or table. Anywhere else they stay text, with a warning.
- **The numbers are written in, and do not renumber themselves — unless you ask.** Every
  chapter, heading, list and caption number is text the build worked out, so the file reads the
  same in all five applications. A reader who inserts a chapter or a table in the .docx
  renumbers from there by hand; the contents, the list of tables and the list of figures still
  fill in, and page numbers still update. **Change the Markdown and build again** — every number
  is worked out afresh. For a thesis its author will go on editing in Microsoft Word, build with
  `--auto-numbering`: Word then counts and renumbers, in Arabic or Thai digits. Other
  applications draw that file differently — LibreOffice writes `ตารางที่ บทนำ-ก` — so read
  [numbering.md](numbering.md) before you offer it.
- **Lists:** `<!-- toc -->`, `<!-- list-of-tables -->`, `<!-- list-of-figures -->` are filled in
  by the build; their page numbers appear once fields are updated ([limits.md](limits.md) §3); write the heading above each yourself. Do not add `--toc` as
  well: it puts a second table of contents on the cover, and the build warns so. A flag
  whose region or caption the document lacks is warned about too — pass the warning on.

## Flags — only for words the user said

Everything above is the default. Add a flag only when the user's request asks for what its
row names, in those words or plainly the same; a request that names none of them gets none.

| the user asks for | flag |
|---|---|
| page numbers | `--page-numbers` (top right); `bottom-center` or `top-center` only when they say where |
| no number on the first page of each section | `--no-page-number-first`, with `--page-numbers` |
| front pages numbered i ii iii, I II III or 1 2 3 | `--front-page-numbers lower-roman`, `upper-roman` or `decimal` |
| numbered sub-headings: 1.1, 1.1.1 (and ก.1 in appendices) | `--heading-numbers` |
| appendices lettered A B C, numbered 1 2 3 or I II III | `--appendix-numbers upper-letters`, `decimal` or `upper-roman` |
| another word than บทที่, ภาคผนวก, ตารางที่ or รูปที่ | `--chapter-label`, `--appendix-label`, `--table-label`, `--figure-label` |
| the chapter title on its own line under "บทที่ 1" | `--chapter-title-on-new-line` |
| Thai digits (๑ ๒ ๓) in page, heading, list, caption and footnote numbers | `--thai-digits` |
| A caption that runs to a second line, indented under its text rather than under its number | `--caption-hanging-indent 0.75` (inches; independent of `--indent`) |
| A caption no wider than the picture above it, and a picture centred on its line | `--caption-matches-object`, `--center-images` |
