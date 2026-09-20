# 2026-09-20 — SARA AM in WPS Writer: seven rounds to one attribute

What [ADR 0038](../adr/0038-the-thai-language-is-written-only-when-asked.md) rests on.

- **WPS Writer 11.1.0.11723** (flatpak, Kingsoft) and **LibreOffice 26.8** on the maintainer's
  Linux machine; **Word 365 for Windows** in three Windows virtual machines (`win10-work`,
  `win10-study`, `win10-legacy`), each with Thai among its languages.
- Every probe was opened by eye, in both applications, by the maintainer. WPS Writer has no
  headless conversion, so nothing here was measured by a script.
- The text of every probe is the same: `กำหนด ทำงาน ดำเนิน คำสำคัญ สม่ำเสมอ ลำเนา`, sometimes with
  `น้ำ ป้ำ` beside it.

## Where it started

WPS had misplaced ำ in every document this skill builds since the first release, recorded with no
cause. The maintainer wrote the same Thai in WPS itself, saved it as `.docx`, and **ำ was placed
correctly**. That file's runs carry:

```xml
<w:rFonts w:hint="default" w:ascii="TH Sarabun New" w:hAnsi="TH Sarabun New" w:cs="TH Sarabun New"/>
<w:sz w:val="32"/><w:szCs w:val="32"/>
```

— no `<w:cs/>`, and no `<w:lang>` at all. This skill writes both. Opened in Word, that same
WPS-written file shows the faults this skill exists to answer: Thai proofed as Latin, wrong word
breaking, wrong spacing. So its way is not a way to copy; it is a clue.

## The seven rounds

Each round changed one thing and kept everything else fixed.

| round | what varied | what it said |
|---|---|---|
| 1 | run properties, inside WPS's own package: no marks / `w:lang bidi` / `<w:cs/>` / both / `w:hint` | `<w:cs/>` alone is **correct**; anything with `w:lang w:bidi="th-TH"` is wrong; `w:hint` changes nothing |
| 2 | our package, run properties varied | all four wrong — our *defaults* already carried the language |
| 3 | our package, `w:bidi` removed from the defaults and from `themeFontLang` | still wrong: the `Normal` style's own `w:lang` still carried it (my error, found by counting the attribute in the file afterwards) |
| 4 | WPS's package with one of our parts swapped in | only `styles.xml` broke it; our `settings.xml` and our `theme1.xml` did not |
| 5 | our `styles.xml` with one property dropped | dropping `<w:lang>` from the defaults **and** `Normal` makes it correct; dropping the East Asian font, `<w:cs/>` or the sizes does not |
| 6 | `<w:lang>` cut down to one attribute | `w:val="en-US"` correct · `w:eastAsia="en-US"` correct · **`w:bidi="th-TH"` wrong** · `w:val`+`w:bidi` wrong · our own package with `w:bidi` alone wrong |
| 7 | the same probes in two more Windows machines | Word draws Thai correctly and underlines nothing Thai in all of them, with or without the attribute |

**The answer: `w:bidi="th-TH"`, wherever it is in effect — a run, a style, or the document's
defaults. Nothing else in the package matters.**

## Two details worth keeping

**A ำ under another mark is drawn correctly.** `น้ำ` and `ป้ำ` come out right in every probe where
plain ำ is wrong, so it is the ordering of marks above the letter that WPS gets wrong, not the
character or the font.

**WPS also swallows a space** between `น้ำ` and `ป้ำ` on screen. Word, on the same bytes, shows the
one space that is there, so nothing is missing from the document.

## What it does not prove

**That a document without the attribute is safe on a machine whose complex-script language is not
Thai.** All three Windows machines have Thai; none of them can answer that question, and ADR 0038
decides the default knowing it. The flag `--thai-language` is what a user reaches for when they
need the guarantee, and the pages that name it say WPS will misplace ำ in that document.

**That other Thai marks are unaffected.** Only SARA AM was looked at closely.

## The probes

Built by hand from the maintainer's own WPS file and from this skill's output, not by the build:
they carry deliberate defects and are not examples to copy. They live outside the repository, in
the maintainer's `Documents/docx/`.
