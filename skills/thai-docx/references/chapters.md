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

![](chart.png)

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
- **Lists:** `<!-- toc -->`, `<!-- list-of-tables -->`, `<!-- list-of-figures -->` fill in
  when Word opens the file; write the heading above each yourself. Do not add `--toc` as
  well: it puts a second table of contents on the cover, and the build warns so. A flag
  whose region or caption the document lacks is warned about too — pass the warning on.

## Flags — only for words the user said

Everything above is the default. Add a flag only when the user's request asks for what its
row names, in those words or plainly the same; a request that names none of them gets none.

| the user asks for | flag |
|---|---|
| page numbers | `--page-numbers bottom-center` (or `top-center`, or `--page-numbers` for top right) |
| no number on the first page of each section | `--no-page-number-first`, with `--page-numbers` |
| front pages numbered i ii iii, I II III or 1 2 3 | `--front-page-numbers lower-roman`, `upper-roman` or `decimal` |
| numbered sub-headings: 1.1, 1.1.1 (and ก.1 in appendices) | `--heading-numbers` |
| appendices lettered A B C, numbered 1 2 3 or I II III | `--appendix-numbers upper-letters`, `decimal` or `upper-roman` |
| another word than บทที่, ภาคผนวก, ตารางที่ or รูปที่ | `--chapter-label`, `--appendix-label`, `--table-label`, `--figure-label` |
| the chapter title on its own line under "บทที่ 1" | `--chapter-title-on-new-line` |
| Thai digits (๑ ๒ ๓) in page, heading and caption numbers | `--thai-digits` |
