# 2026-09-19 — WPS Writer, re-checked

`ROADMAP.md` has carried this since 0.1.0: two fixes landed after the last WPS check
([2026-09-16](2026-09-16-office-check-five-applications.md)) and nobody had opened the files in WPS
since. This is that check.

- **WPS Writer 11.1.0.11723**, part of WPS Office (Kingsoft, 2024), on Ubuntu 24.04.
- The four files of the release oracle, byte-identical to `tests/golden/`, built from `main`
  **ada622e**: `sample-basic`, `sample-text`, `sample-options`, `sample-layout`.
- Word 365 for Windows remains the reference (ADR 0012). What WPS draws its own way is recorded,
  not chased.

## The two fixes, seen for the first time in WPS

**The line before a hard break no longer spreads, under `--align thai`.** In `sample-options`, at
200 %, the line

> `+ S องค์ประกอบเหล่านี้ต้องแสดงผลได้ถูกต้องเช่นเดียวกับข้อความภาษาไทยทั่วไป`

sits normally, with ordinary word spacing, and the hard break follows it. Before
`w:doNotExpandShiftReturn` it spread letter by letter across the page. **Fixed, and now confirmed
in the application it was fixed for.**

**A heading's number takes the heading's own size, font and weight.** In `sample-text`, `1.1` is
bold blue at the heading's size, `1.3.1` is italic at its own; the number no longer comes out at the
application's default size beside a large heading. **Fixed, confirmed.**

## The two things the ADR 0027 fixes had to hold

**All three lists show their entries.** สารบัญ, สารบัญตาราง and สารบัญภาพ each carry their entries
and page numbers — ก ข ค ง ฉ ช for the front matter, then 1, 2, 4, 6 — in `sample-text` and in
`sample-layout`.

They are filled **on open, not by the reader**: the entries are in the field's result inside the
file, which the package shows directly —

```
field instruction: TOC \o "1-3" \h \z \u
result:            บทคัดย่อ · Abstract · กิตติกรรมประกาศ · สารบัญ · สารบัญตาราง · สารบัญภาพ ·
                   บทที่ 1 บทนำ · ความเป็นมาและความสำคัญของปัญหา · …
```

That is what ADR 0027 decided, and WPS is the reader it was decided for.

**The entries keep their font.** TH Sarabun New throughout, after References → Update, in both
files. The `Hyperlink` style naming a font is holding.

## What WPS still draws its own way

**Thai in `w:lvlText` goes through a legacy code page.** `บทที่ %1` comes out as

> **`ÓõõõyA 1 บทนำ`**

unchanged from 2026-09-16. The Latin digit survives and the Thai does not, which is the shape of a
code-page conversion rather than a missing font. Not ours to fix: the bytes say `บทที่`, and Word,
Word on the web and Google Docs all draw it.

**SARA AM (ำ) is still placed wrongly.** At 210 %, `ความสำคัญ` and `จัดทำเอกสาร` show the nikhahit
over the preceding consonant instead of over the ำ's own base. Unchanged, in heading and in body.

## Two things this check found that the last one did not

**With `--thai-digits`, the numbering value 1 comes out as ๕.** In `sample-options`, where Word
shows ๑, WPS shows ๕ — in the chapter number (`ÓõõõyA ๕`), in heading numbers (`๕.๕`, `๕.๒`) and in
numbered list items. **2 and 3 are right** (๒, ๓), and the **footnote markers are right** (๑, ๒), so
it is not the font and not the digit itself: it is the same numbering path that mangles `บทที่`.
Captions are right too (`ตารางที่ ๑-๑`) — those are text the build writes, not a number the reader
renders.

A reader that draws 1 as 5 is worse than one that draws a label as Latin letters, because nothing
about it looks wrong. Recorded as a WPS difference; there is nothing in the file to change.

**The task-list boxes do not appear at all.** `☐ งานที่ยังไม่ทำ` and `☑ งานที่ทำแล้ว` render with
their text and no box. The reason is in the file and is not WPS's fault:

```xml
<w:rFonts w:ascii="Segoe UI Symbol" w:hAnsi="Segoe UI Symbol" w:cs="Segoe UI Symbol"/>
```

**Segoe UI Symbol is a Microsoft font, and this machine does not have it.** On Windows the boxes
draw; on this Ubuntu machine no font is asked for that carries U+2610 and U+2611, so nothing is
drawn. Item 9 of ADR 0012's list — "☐ and ☑ show as symbols" — therefore **fails on Linux, in any
reader**, and the last check did not catch it because the Linux readers were looked at for other
things.

This one **is** ours, and it is a decision rather than a patch: name a font that exists where the
document will be read, or use characters an ordinary Thai font carries. It is written up beside the
other two decisions waiting on the maintainer.

## The ordinary checks

Everything else of ADR 0012 holds in all four files: nothing missing against the Markdown; bold and
italic on Thai; strikethrough; bullets at three levels and numbered lists counting on; Thai lines
breaking inside words; TH Sarabun New applied, at 15 pt where `--size 15` asked; tables with their
borders and repeating headers; links; footnotes numbered at the foot of their page with a
separator; `H₂O` and `x²`; the image inside the page; F14 landscape in `sample-layout`; the header
and footer of `sample-options`; Thai distributed alignment.

`sample-layout`'s own three: F14 landscape ✓, the table header not repeating (`--no-repeat-table-header`) ✓,
no spelling squiggles (`--hide-spelling-errors`) ✓.

## What this changes

| | |
|---|---|
| ROADMAP's WPS item | done; 0.2.0's fourth item closes |
| the 2026-09-16 record | two of its findings are now fixed-and-seen; two are unchanged and stay recorded as differences |
| new | the `--thai-digits` numbering difference, and the missing symbol font — the second needs a decision |

Nothing in this check asks for a byte to change in what the build writes, except the symbol font,
which is a decision.
