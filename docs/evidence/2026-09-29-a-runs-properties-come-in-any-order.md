# 2026-09-29 — a run's properties come in any order

What this proves: the schema lets a run's properties come in any order, and Word 365 for Windows
uses every one of them whatever the order. Only `<w:rPrChange>`, the record of a revision, has a
place: after them. From 0.3.2 `check` reports `order` in a run's properties only for that, and
`repair` moves nothing else there.

Until now `check` reported, and `repair` put right, a run's properties out of the order the first
edition of the schema fixed, on the ground that "Word ignores a property that stands in the wrong
place" ([2026-09-19](2026-09-19-repair-puts-the-properties-back-in-order.md), `ooxml.py`). No record
measured that sentence.

## The schema

`EG_RPrContent`, which `CT_RPr` holds, in the three editions:

| edition | `EG_RPrBase` | so |
|---|---|---|
| 1st, 2006, Part 4 | `xsd:sequence`, every child `minOccurs="0"` | the order is fixed |
| 5th, 2016, Part 4 Transitional (`wml.xsd:1818`, `:1861`) | `xsd:choice`, the group `minOccurs="0" maxOccurs="unbounded"`, then `rPrChange` | any order; `rPrChange` last |
| 5th, 2016, Part 1 Strict (`wml.xsd:1741`, `:1784`) | the same | the same |

The 39 names come in the same order in all three, and `rpr_order` in `assets/ooxml.json` was that
list with `rPrChange` after it. In the 2016 edition `CT_PPrBase`, `CT_SectPr`, `CT_Settings` and
`CT_TblPrBase` are still sequences: their `order` stays as it was. `CT_TrPrBase` is a choice, which
`check` already read as one.

## Word 365 for Windows

The maintainer opened a test file built from one document by the skill, each line a run whose
properties were swapped, beside a line in order as its control:

| line | the run's properties | seen |
|---|---|---|
| 00 | `b color sz` (control) | bold, coloured, sized |
| 01 | `sz color b` | as 00 |
| 02 | `color b` | as expected |
| 03 | `sz rFonts` (Courier New) | as expected |
| 04 | `u i` | as expected |
| 05 | `vertAlign` (superscript) `b` | as expected |
| 06 | `bCs szCs cs`, Thai (control) | bold, sized |
| 07 | `cs szCs bCs`, Thai | as 06 |

No message on opening. Every line matched what it was built to show, read on the page and on the
Home tab. Saved as a new file with nothing changed, Word kept every property and wrote each run's
back in the order of the list: `sz color b` → `b color sz`, `cs szCs bCs` → `bCs szCs cs`.

Files: the test file sha256 `f297988c…82e0`, the file Word saved `f889730a…29dc`.

## What changed

- `rpr_order` is one place for the 39 names, then `rPrChange` (the form `trpr_order` already had).
  `check` reports `order` in a run's, a paragraph mark's, a style's or a level's `w:rPr` only when
  `<w:rPrChange>` is not last; `repair` moves only that.
- Where `repair` adds a property (`<w:cs/>`, a twin), it still puts it where Word writes it, so a
  file it repairs keeps the bytes it had. No golden moves.
- ADR 0004's sentence that "a property in the wrong position can be ignored" carries a Later note,
  and so does the record of 2026-09-19.
