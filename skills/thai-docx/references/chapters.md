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
- **Pages:** every `#` starts a new page (a section). Page numbers show only with
  `--page-numbers` (e.g. `--page-numbers bottom-center`). The cover has no page number; front
  pages count ก ข ค (`--front-page-numbers lower-roman`, `upper-roman` or `decimal` for
  i ii iii, I II III, 1 2 3); the chapters restart at 1 and the rest go on from there.
  With `--page-numbers --no-page-number-first`, the first page of every section has none.
- **Chapters:** in `chapters`, `#` reads "บทที่ 1 บทนำ" (`--chapter-label`); add
  `--heading-numbers` for 1.1, 1.1.1.
- **Appendices:** in `appendices`, `#` reads "ภาคผนวก ก แบบสอบถาม" (`--appendix-label`;
  `--appendix-numbers upper-letters`, `decimal` or `upper-roman` for A, 1, I); with
  `--heading-numbers`, `##` reads ก.1. Headings in the cover, `front` and `back` have no
  number.
- **Captions:** `Table:` just before a table and `Figure:` just after an image alone in its
  paragraph become "ตารางที่ 1-1 …" and "รูปที่ 1-1 …" in a chapter, "ตารางที่ ก-1 …" in
  an appendix, "ตารางที่ 1 …" elsewhere or with no region comments (`--table-label`,
  `--figure-label`). Leave a blank line between a caption and its image or table.
  Anywhere else they stay text, with a warning.
- **A chapter heading on two lines:** `--chapter-title-on-new-line` puts "บทที่ 1" on its
  own line and the chapter's title under it, in the chapters and the appendices; the lists
  still read it as one line. Without the flag the number and the title share a line.
- **Lists:** `<!-- toc -->`, `<!-- list-of-tables -->`, `<!-- list-of-figures -->` fill in
  when Word opens the file; write the heading above each yourself. Do not add `--toc` as
  well: it puts a second table of contents on the cover.
- **Flags:** ก ข ค front pages, "ภาคผนวก ก" and Arabic digits are the defaults; add
  `--front-page-numbers`, `--appendix-numbers` or `--thai-digits` only when asked.
