# 2026-09-19 — three of the five applications, on the release bytes

The check ADR 0012 asks for before a release, on the files built from `main` **dcd60eb** — the bytes
v0.2.0 will carry. Three applications of the five; Word for macOS and Google Docs are still owed.

| application | where | files opened |
|---|---|---|
| WPS Writer | 11.1.0.11723, Ubuntu 24.04 | `sample-basic`, `sample-options` |
| Word 365 | Windows 10 | `sample-basic`, `sample-options` |
| LibreOffice Writer | Linux | `sample-basic`, `sample-options` |

**The machine had fonts installed since the last round.** Until 2026-09-18 the only font added to it
was TH Sarabun New; everything else was what the operating system ships. This round was taken after
the maintainer installed the fonts the documents ask for. That single fact explains most of what
follows, and it is why the readings are reported with it attached rather than as bare observations.

## The two changes this check was called for

**The task-list box draws.** `□` unchecked and `■` checked, in all three applications, in the body
of `sample-basic` and of `sample-options` and in Appendix A's questionnaire. (On the Linux machine
this no longer isolates the cause, since the symbol font was installed there too — but the file
being drawn is the one ADR 0033 wrote, and it draws.)

**บทคัดย่อ and Abstract are centred alike**, in all three. Before
[the fix](2026-09-19-an-english-heading-is-a-heading.md) the English one was flush left in every
reader, because the paragraph overrode its own style.

## WPS Writer — two recorded "limitations" were a missing font

[This morning's record](2026-09-19-wps-writer.md) reported, and
[2026-09-16's](2026-09-16-office-check-five-applications.md) before it, that WPS draws Thai in
`w:lvlText` through a legacy code page — `บทที่ ๑` as `ÓõõõyA` — and that with `--thai-digits` the
numbering value 1 comes out as `๕`.

**With the fonts installed, both are gone.** The same document now shows

> **บทที่ ๑ บทนำ** · **๑.๑ ความเป็นมาและความสำคัญของปัญหา** · **๑.๔ ประโยชน์ที่คาดว่าจะได้รับ** ·
> `ตารางที่ ๑-๑` · `รูปที่ ๒-๑` · `ตารางที่ A-๑` · `รูปที่ B-๑`

and all three lists fill with the right numbers after References → Update:

> สารบัญ: บทที่ ๑ บทนำ … ๑ · ๑.๑ ความเป็นมาและความสำคัญของปัญหา … ๑ · ๑.๒ … ๒
> สารบัญตาราง: ตารางที่ ๑-๑ … ๓ · ตารางที่ ๒-๑ … ๔ · ตารางที่ ๔-๑ … ๙ · ตารางที่ A-๑ … ๑๔
> สารบัญภาพ: รูปที่ ๒-๑ … ๕ · รูปที่ ๓-๑ … ๗ · รูปที่ ๔-๑ … ๑๑ · รูปที่ B-๑ … ๑๕

Front matter counts i ii iii iv v vii viii; the body counts ๑ ๒ ๓; captions, appendix labels and
page numbers all agree with Word.

**So the earlier readings were of a machine, not of WPS.** A numbering level's run names
TH Sarabun New, which was present; what was missing was whatever WPS falls back to while it draws
`w:lvlText`, and a font without Thai draws Thai bytes as the Latin letters its own encoding has —
which is exactly the shape `ÓõõõyA` has, and exactly the shape ADR 0033 found behind the missing
task box. **Two findings, one cause, and the cause is not in the file.**

This is the second time in two days that "the application cannot do it" turned out to be "the
machine had not been given the font". The 2026-09-16 and 2026-09-19 WPS records are corrected by
this one; what stays recorded for WPS is **SARA AM's placement**, which is unchanged.

The maintainer has not yet named which fonts were installed. That list belongs in this record, and
is the one thing here still to fill in.

## LibreOffice Writer — two differences, and a distinction that matters

Both concern **numbering formats and fields**. Neither is in the bytes: Word draws the same file
correctly. What LibreOffice does depends on whether the reader has updated fields, and the two
halves behave differently.

**Before any field is updated** — the file as it arrives — the three lists are right:
`ตารางที่ ๑-๑`, `รูปที่ ๒-๑`, `บทคัดย่อ`, `Abstract`, in Thai digits, because
[ADR 0027](../adr/0027-lists-carry-entries-and-runs-name-their-font.md) writes the field's result
into the package. That is the decision working exactly as it was meant to.

But two things are wrong from the moment the file opens, with no update at all:

**1. `thaiNumbers` is not honoured.** Headings read `บทที่ 1`, `1.1`, `1.3.2`, `2.1` where Word and
WPS give `บทที่ ๑`, `๑.๑`, `๑.๓.๒`, `๒.๑`. Numbering is not a field — nothing is being recomputed,
the format is simply not supported. The file asks plainly:

```xml
<w:numFmt w:val="thaiNumbers"/><w:lvlText w:val="บทที่ %1"/>
```

**2. A caption's number is rebuilt, wrongly, at load.** LibreOffice re-evaluates `STYLEREF` and
`SEQ` when it opens the document, discarding the written-in result, and gets both halves wrong:

| in the file | Word and WPS | LibreOffice |
|---|---|---|
| `STYLEREF 1 \s` | `๑` — the heading's number | **`บทนำ`** — the heading's text |
| `SEQ Table \* ThaiArabic \s 1` | `๑`, restarting each chapter | **`ก`, `ข`, `ค`, `ง`, `จ`** — Thai letters, never restarting |

so the caption reads **`ตารางที่ บทนำ-ก`**, and later **`ตารางที่ ผลการตรวจสอบความเที่ยงตรงของเครื่องมือ-จ`**.
When the reader then updates the lists, the lists pick up the same wrong text.

**This is the one finding here that a reader would call a defect**, and it is worth stating plainly
what the choice is. Nothing can make LibreOffice evaluate those fields as Word does. The caption
number could instead be written as literal text — the build knows it at build time — which would be
right in every application and would stop Word renumbering captions when a user edits the document.
That is a trade, and a decision, not a patch: ADR 0021 chose fields deliberately. **Recorded here,
for the maintainer to decide; nothing is changed on the strength of this record.**

Everything else in LibreOffice holds: the boxes, both abstract headings centred, Thai distributed
paragraphs, the quote in italic, tables and their borders, the image, footnotes, the code block in
its own font, TH Sarabun New throughout, both appendices' headings.

## Still owed

| | |
|---|---|
| **Word for macOS** | never opened; ADR 0012's long-standing gap |
| **Google Docs** | not in this round |
| the font list | which fonts were installed on the Linux machine between the two rounds |
