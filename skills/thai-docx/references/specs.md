# Specs: everything the Markdown can say

Read this when the user wants a document of a particular shape — a letter, a report, a form,
a thesis — and you are writing the Markdown for it (SKILL.md, Build a document). It is the whole
surface in one page: what the format can express, what stops the build, and what only warns.

**This describes a format, not a house style.** The skill carries no ministry's, university's or
company's form, and never will. When the user shows you one of their own — a PDF, a .docx, a
photograph of a page — read theirs and write Markdown that matches it. When they show none, keep
it plain and say so; do not ask, and do not invent an official format for them.

## The way through

1. Read what the user gave you: their example, their text, or what you agreed earlier.
2. Write the Markdown. Say which parts of their example you could express and which you could not.
3. Show it to them, or write it to a file, in the same reply as the build, so they can correct it
   afterwards.
4. Build it — `python3 <skill>/scripts/thai_docx build doc.md doc.docx [flags]`.
5. If they like the result and want it again, `profile save <name> [the same flags]`.

## One document that uses every construct

````markdown
---
title: รายงานตัวอย่าง
author: ผู้เขียนตัวอย่าง
heading-1: font-size: 20pt; text-align: center
heading-2: font-size: 18pt; color: #1F4E79
---

# หัวข้อใหญ่

ย่อหน้าธรรมดา มี **ตัวหนา** *ตัวเอียง* ~~ขีดฆ่า~~ `โค้ดในบรรทัด` <u>ขีดเส้นใต้</u>
สูตร H<sub>2</sub>O และ x<sup>2</sup> ปุ่ม <kbd>Ctrl</kbd> และ[ลิงก์](https://example.org/)
กับเชิงอรรถ[^1] บรรทัดนี้ลงท้ายด้วยช่องว่างสองตัว  
จึงขึ้นบรรทัดใหม่ในย่อหน้าเดียวกัน

[^1]: เชิงอรรถอยู่ท้ายหน้าที่อ้างถึง

## หัวข้อรอง

- รายการแบบจุด
  - ซ้อนชั้น
- [ ] งานที่ยังไม่ทำ
- [x] งานที่ทำแล้ว

1. รายการแบบเลข
2. ข้อถัดไป

> ข้อความที่ยกมา

```text
โค้ดในกรอบ
```

| คอลัมน์ | ตัวเลข | หมายเหตุ |
|---|---:|:---:|
| ก | 1 | ชิดขวาและกึ่งกลาง |

---

![คำอธิบายภาพ](figure.png)
````

That block builds with no warning. Everything below says what else is possible.

## Blocks

| | how |
|---|---|
| heading, six levels | `#` … `######` |
| paragraph | a line, or lines; a break between two Thai characters joins them with no space |
| line break inside a paragraph | two spaces at the end of the line, or `<br>` |
| bullet list, nested | `-` and two spaces per level |
| numbered list | `1.` `2.` — the number you write is where it starts |
| task list | `- [ ]` and `- [x]`, drawn as □ and ■ |
| quotation | `>` |
| code | three backticks, or four spaces |
| table | `\| … \|` with `---`, `---:` or `:---:` for alignment |
| rule | `---` |
| footnote | `[^name]` where it is read, `[^name]: text` anywhere |
| image | `![alt](file.png)` — PNG or JPEG, in the Markdown's folder or below it |

## Inline

`**bold**`, `*italic*`, `~~strike~~`, `` `code` ``, `[text](url)`, `<https://example.org/>`,
`<u>`, `<sup>`, `<sub>`, `<kbd>`, `<br>`, HTML comments (removed), and entities such as
`&nbsp;` and `&amp;`, which CommonMark resolves to the character itself.

## The shape of a long document

| | how | reads as |
|---|---|---|
| regions | `<!-- front -->`, `<!-- chapters -->`, `<!-- back -->`, `<!-- appendices -->`, `<!-- back -->` — in that order, each once, any left out | every `#` starts a page; chapters and appendices number their headings |
| table caption | a paragraph `Table: ข้อความ` **just before** the table | ตารางที่ 1-1 ข้อความ |
| figure caption | a paragraph `Figure: ข้อความ` **just after** an image alone in its paragraph | รูปที่ 1-1 ข้อความ |
| contents | `<!-- toc -->` | filled in, with its heading written by you above it |
| list of tables, of figures | `<!-- list-of-tables -->`, `<!-- list-of-figures -->` | the same |

The labels are settings, not fixed words: `--chapter-label`, `--appendix-label`,
`--table-label`, `--figure-label`. Details and the rules in
[chapters.md](chapters.md); an example document and profile in
[../examples/README.md](../examples/README.md).

## Front matter

Flat `key: value` lines between `---` lines at the very top, nothing nested.

| key | effect |
|---|---|
| `title`, `author` | the document's properties |
| `heading-1` … `heading-6` | how that heading level looks — the properties are in [heading-styles.md](heading-styles.md) |
| anything else | ignored |

## Everything a flag can set

Paper, margins, font, size, line spacing, indent, alignment, page numbers, headers and footers,
Thai digits, table widths, and the labels above: the whole table is
[settings.md](settings.md), which is generated from the build's own registry. A profile holds
the same settings under a name ([profiles.md](profiles.md)).

## What stops the build

It stops rather than writes a file it is unsure of, and names the line — for a picture, its path (exit 2):

- an HTML tag that is not one of the five above, or one of them alone on its own line — rewrite it
  as Markdown; `<?…?>`, `<!DOCTYPE …>`, `<![CDATA[…]]>`; a comment never closed, or text after a
  comment on its line;
- a link to anything but `http`, `https` or `mailto` (a link with no scheme is written as it is);
- a character a reader cannot see: a zero-width character, a soft hyphen, a direction mark, any
  other format character, a noncharacter;
- blocks or inline formatting nested more than 100 deep;
- a footnote defined but never referenced, or defined twice; a table row with more cells than its
  header; region comments out of order or twice;
- an image that is missing, remote, not PNG or JPEG, not whole, wider or taller than 20,000
  pixels, outside the Markdown's folder (unless `--allow-dir` names one), or too large for a .docx;
- a front matter declaration or a flag value outside what [settings.md](settings.md) allows.

## What only warns

The file is written; pass the warnings on. An image with nothing between the brackets of `![]`;
a heading level skipped; a link definition nobody uses; `ำ` typed as `ํ` + `า`; a paragraph that
opens with `ตาราง:` or `รูป:` where a caption would go — the prefix is `Table:` or `Figure:`, in
English, in every language; a `Table:` or `Figure:` line where no caption can go; a region comment
inside a list, quotation or footnote; a font not known to carry Thai; `--toc` beside `<!-- toc -->`;
`$…$` math, kept as literal LaTeX; a picture too narrow for a caption of its width; a flag whose
structure the document has not got; and `--thai-language` with no Thai text to reach.

## Writing Thai

Do not put spaces between Thai words to force a line break: the build marks Thai as complex script so
the application breaks inside words by itself, and a space would be wrong in the text. Wrapping a long
Thai line in the Markdown is safe. The text in the file is the user's, character for character —
the build refuses to write a document whose text differs from the Markdown by one character.
