# Settings

Generated from the settings registry by `tools/gen_settings_docs.py`; do not edit by hand.

The defaults, and the flag that changes each one. Add a flag only for what the user asked
for; every other setting keeps its default.

## Page and type

Every document has these.

| setting | default | flag |
|---|---|---|
| font | TH Sarabun New | `--font "Sarabun"` |
| size | 16 pt | `--size 14` (1–400) |
| paper | A4 | `--paper letter` or `--paper f14` (8.5 × 13 in) |
| orientation | portrait | `--landscape` (margins stay top, right, bottom, left) |
| margins, inches | 1, 1, 1, 1.5 (top, right, bottom, left) | `--margins 1,1,1,1` |
| first-line indent, inches | none | `--indent 0.5` (body paragraphs only; not a picture alone in its paragraph) |
| line spacing | 1 | `--line-spacing 1.5` (1–3; code and footnotes stay single) |
| alignment | left | `--align thai` (Thai distributed; a paragraph with no Thai stays left) |
| the complex-script language of the text | left to the reader's machine | `--thai-language` (writes `w:bidi="th-TH"`; see [limits.md](limits.md) §3) |
| which runs are marked complex script | the runs whose text is complex script | `--force-cs-whole-doc` (every run, as releases before 0.2.0 wrote: one font throughout, and an application underlines correctly spelled English on screen) |
| spelling squiggles | shown | `--hide-spelling-errors` |

Without a run that is not Thai (a number, a Latin word, a footnote's mark), `--force-cs-whole-doc` changes nothing, and the build says so.

## Page furniture

The header and footer, how numbers are drawn, and who counts them.

| setting | default | flag |
|---|---|---|
| page numbers | none | `--page-numbers` (top right), `--page-numbers top-center` or `--page-numbers bottom-center` |
| page number on the first page of each section | shown | `--no-page-number-first` (with `--page-numbers`) |
| header text | none | `--header "ลับ"` (centred, above a page number there) |
| footer text | none | `--footer "TEXT"` (centred, above a page number there) |
| page, heading, list, caption and footnote numbers | 1 2 3 | `--thai-digits` (๑ ๒ ๓; the text itself is never changed) |
| heading, list and caption numbers | written by the build, the same in every application | `--auto-numbering` (the application counts, and Word renumbers as you edit; what each application draws is in [numbering.md](numbering.md)) |

Without a numbered heading, an ordered list or a caption, `--auto-numbering` changes nothing, and the build says so.

## Tables

How tables are laid out.

| setting | default | flag |
|---|---|---|
| table header row | repeats on every page | `--no-repeat-table-header` |
| table column widths | equal | `--table-widths auto` (wider for longer text) |
| table text size | as the body | `--table-size 14` (1–400) |

Without a table, `--no-repeat-table-header` and `--table-widths` change nothing, and the build says so.

## Headings

How headings are numbered and listed.

| setting | default | flag |
|---|---|---|
| table of contents | none | `--toc` (at the top of the document) |
| heading numbers | none | `--heading-numbers` (1. for `#`, 1.1 for `##`, 1.1.1 …) |

`--toc` beside a `<!-- toc -->` comment makes a second table of contents, and the build says so.

## Thesis structure

For a report or thesis: region comments and `Table:` / `Figure:` captions — [chapters.md](chapters.md).

| setting | default | flag |
|---|---|---|
| chapter label | บทที่ | `--chapter-label "บท"` |
| table caption label | ตารางที่ | `--table-label "ตาราง"` |
| figure caption label | รูปที่ | `--figure-label "ภาพที่"` |
| caption lines after the first | start at the margin, like the first | `--caption-hanging-indent 0.75` (0–4 in; independent of `--indent`) |
| an image on a line of its own | starts at the left margin | `--center-images` |
| the width of a caption | the width of the text | `--caption-matches-object` (as wide as the picture it belongs to; a picture too narrow to leave an inch gives its caption the text width, and the build says so) |
| page numbers before the chapters | ก ข ค | `--front-page-numbers lower-roman` (or `upper-roman`, `decimal`) |
| appendix label | ภาคผนวก | `--appendix-label "Appendix"` |
| appendix numbers | ก ข ค | `--appendix-numbers upper-letters` (or `decimal`, `upper-roman`) |
| chapter title | beside its number | `--chapter-title-on-new-line` (บทที่ 1 on one line, the title under it) |

Without a `#` heading under `<!-- chapters -->`, `--chapter-label` changes nothing, and the build says so.

Without a `Table:` caption, `--table-label` changes nothing, and the build says so.

Without a `Figure:` caption, `--figure-label` and `--caption-matches-object` change nothing, and the build says so.

Without a `Table:` or `Figure:` caption, `--caption-hanging-indent` changes nothing, and the build says so.

Without an image on a line of its own, `--center-images` changes nothing, and the build says so.

Without a `<!-- front -->` comment, `--front-page-numbers` changes nothing, and the build says so.

Without a `#` heading under `<!-- appendices -->`, `--appendix-label` and `--appendix-numbers` change nothing, and the build says so.

Without a `#` heading under `<!-- chapters -->` or `<!-- appendices -->`, `--chapter-title-on-new-line` changes nothing, and the build says so.
