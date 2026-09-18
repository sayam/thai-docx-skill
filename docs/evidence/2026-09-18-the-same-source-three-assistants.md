# 2026-09-18 — the same Markdown, three assistants

The question behind this record: a general assistant can write a `.docx` today. Given the same
source, does it produce a Thai document this project's checker would pass — and is a skill still
needed?

Two documents were used, from the easiest case to the hardest, with the same three conditions each
time. Every file was checked with `thai_docx check` on the same commit.

## Documents

| | source | what is in it |
|---|---|---|
| **thesis** | `tests/fixtures/thesis/thesis.md` | 303 lines, 15 987 characters, 5 tables (57 rows), 2 images, 2 footnotes, this project's own region comments and `Table:`/`Figure:` captions |
| **plain report** | 133 lines, 12 458 characters | ordinary CommonMark only: one `#`, four `##`, ten `###`, long Thai paragraphs, one bullet list, one 50-row table that runs over two pages. No front matter, no directives, no images, no footnotes |

## Conditions

| condition | how it was asked |
|---|---|
| **skill, named** | Claude Haiku 4.5, `/thai-docx สร้างไฟล์ docx จาก …` |
| **no brief** | ChatGPT: "สร้างไฟล์ Word (.docx) จากไฟล์ Markdown ที่แนบมา…" and nothing else |
| **full brief** | ChatGPT, given a written specification of every directive, every numbering rule and the page setup, plus "do not change a single character" — everything except the words *complex script*, `<w:cs/>`, `w:lang` and `szCs`, which are what was being measured |

The full brief was run on the thesis only.

## The thesis

| | Haiku + skill | ChatGPT, no brief | ChatGPT, full brief |
|---|---|---|---|
| **findings** | **0** | **707** | **203** |
| code 2 — run with text, no `<w:cs/>` | 0 | 584 (every run) | 199 (every run) |
| code 4 — word split across runs | 0 | 106 | 3 |
| code 5 | 0 | 15 | 0 |
| code 3 | 0 | 1 | 1 |
| properties out of order | 0 | 1 | 0 |
| `<w:cs/>` elements | 584 | 0 | 0 |
| runs marked as Thai | 585 | 1 | 1 |
| tables | 5 | 5 | **0** |
| images embedded | **2** | 0 | 0 |
| footnotes part | yes | yes | no |
| TOC fields | 3 | 1 | 0 |
| paragraphs holding raw Markdown | 4 | 4 | **113** |
| text characters (source 15 987) | 14 810 | 14 956 | 15 685 |
| bytes | 189 515 | 44 506 | 30 899 |

## The plain report

| | Haiku + skill | ChatGPT, no brief |
|---|---|---|
| **findings** | **0** | **346** |
| code 2 | 0 | **343 (every run)** |
| code 5 — bullet level in Symbol font | 0 | 3 |
| `<w:cs/>` elements | 342 | 0 |
| runs marked as Thai | 342 | 0 |
| paragraphs | 343 | 345 |
| table / rows | 1 / 50 | 1 / 50 |
| header row repeats across pages | **yes** | **no** |
| raw Markdown left as text | 0 | 0 |
| text characters (source 12 458) | 11 289 | **11 288** |
| bytes | 119 651 | 29 575 |

## What the numbers say

**The skill's runs are byte-identical to the reference build.** Both of Haiku's files match what
`thai_docx build` writes with no flags, on this machine, from the same source:

```
b7aab940baa27b3a65e1db43865fe71389a17781ef145e1760383eabfbc39b7b   thesis
7b7f91161b21…                                                      plain report
```

Haiku 4.5 did not *write* a correct Thai `.docx`. It chose the right command and let the build write
it, which is what ADR 0008 promises and what a skill is for: a small, cheap model reaches a perfect
result because the knowledge is in its context as a tool rather than as something it must remember.

**ChatGPT builds a good document and gets the script wrong in every run.** The plain report is the
cleanest demonstration. Every heading converted, no raw `#` anywhere, the 50-row table built as a
real Word table, 345 paragraphs against the reference's 343, 11 288 characters against 11 289 — and
`<w:cs/>` on none of its 343 runs, with none marked as Thai. The one correctness defect in the file
is the Thai.

That rules out the easy explanations for the thesis result. It was not the thesis being long, the
brief being clumsy, or this project's directives being unusual. Strip every complication away and
the same thing happens.

**More instruction made it worse, for a reason the brief itself caused.** The briefed run wrote the
Markdown into Word as literal text: 113 paragraphs still carrying `#`, `|`, `**` and `<!-- -->`, no
tables, no footnotes, no TOC. The brief's last rule was *do not change a single character*, and that
is the one instruction a model can check cheaply; turning a Markdown table into a Word table makes
`|` and `---` disappear, which looks like breaking it. The brief never said that markup is not
content. This is one run, and the observation belongs to how the instruction was written as much as
to the model.

## Three smaller findings

**The table header does not repeat.** The reference sets `tblHeader` on the first row of the report's
table; ChatGPT's file has no `tblHeader` at all. The table was written to run over two pages, so page
two carries 25 rows of numbers with no column names. No finding code covers this — a reader notices
it at once and the checker does not.

**One character of the title is gone.** The two files differ by exactly one character, at offset 51:
a space dropped from the document's title (`…เอกสารอิเล็กทรอนิกส์ ประจำปี…` became
`…เอกสารอิเล็กทรอนิกส์ประจำปี…`). Silent, invisible once rendered, and exactly the failure ADR 0023
exists to prevent — which is why the build compares its output against the Markdown paragraph by
paragraph and refuses to write when one character differs.

**The generator writes the signed-in user's name into the file.** Both ChatGPT-produced files carry
`dc:creator` set to the display name of the account that asked for them — in this run, the
maintainer's. The reference build writes `dc:creator` only when the Markdown's front matter sets an
author, and writes no properties at all when it does not: R6 of
[`docs/assurance-case.md`](../assurance-case.md), verified again here by the plain-report build,
which has no front matter and no `dc:creator`.

## Limits of this record

- One document per condition, one run each, one day. The structural findings — no `<w:cs/>`
  anywhere, no Thai language mark, no images embedded — are properties of the files rather than
  judgements, and are as firm as the files. The "brief made it worse" observation is a single run.
- The skill runs measure the tool, invoked by name. Whether a model *finds* the skill unprompted is
  a different question, measured by the agent rounds recorded in
  [`2026-09-16-agents-with-the-grown-skill.md`](2026-09-16-agents-with-the-grown-skill.md).
- Nothing here measures writing quality, and it must not be read as if it did. What is measured is
  whether the knowledge this project wrote down is present anywhere else.
