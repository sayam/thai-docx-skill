# 2026-09-30 — model equivalence on the skill of 0.3.2

> **Later (2026-10-03):** the three fonts are those SKILL.md named for "change the font";
> `references/settings.md` names one.

What this proves: the text 0.3.2 changed where an agent reads it (`grill`'s answer and four
reference pages; SKILL.md is the text of 0.3.1) still leads three models to the file each request
of [the last record](2026-09-29-model-equivalence-on-the-0.3.1-skill-md.md) asks for; a request to
check a .docx, with or without asking for a repair, runs `check` and never `build`; and a font's
name longer than Word reads is built and said. It is also the first run of Sonnet and Opus on the
SKILL.md of 0.3.1 as released. What it does not prove: a rate. Each cell is one to three runs, a
sample and not a measure.

Environment: as in the last record, on Claude Code 2.1.285. Models: `claude-haiku-4-5-20251001`,
`claude-sonnet-5`, `claude-opus-5-5`. Each `claude -p` was capped at US$1. Every turn was billed
to a Console API key (its credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`, in all
58 turns). The traces are the maintainer's working copy and are not part of the repository.

## What an agent reads now that it did not

- **`grill`'s answer** in `"mode": "build"` ends "a .docx the user has goes to check" (V32-04).
  SKILL.md said so already; the script's answer, which SKILL.md says to obey, did not.
- **`references/check.md` and `repair.md`**, row `order`: a run's properties and a paragraph
  mark's come in any order, and only a tracked change's `w:rPrChange` that is not last is reported
  and moved (V32-01).
- **`references/profiles.md` and `limits.md`**: "reached no" is said of a flag typed after a
  profile only, and a font's name past the 31 characters Word reads is written cut, with a warning
  (V31-10, V31-11).

## The files the requests ask for

As in the last record: no golden has moved since 0.3.0.

| case | flags | sha256 |
|---|---|---|
| *sample*, *trigger* | none | `cc1e73ba…c350` (= `tests/golden/sample-default.docx`) |
| *thesis* | `--heading-numbers --page-numbers bottom-center` | `0b64a9d6…77d2` (= `tests/golden/thesis-text.docx`) |
| *change* | `--size 14 --page-numbers` | `be3282d3…8d82` |

## What came back

The eight requests of the last record, and two new ones:

- *checkonly*: "ช่วยตรวจไฟล์ broken.docx ให้หน่อย", on the file of *repair*. It passes when
  `check` runs and neither `build` nor `repair` does: the user asked for no repair.
- *fontlong*: "สร้างไฟล์ Word จาก sample.md ใช้ฟอนต์ TH Sarabun New Extra Condensed Regular
  ตั้งชื่อ report.docx", a name of 38 characters. It passes when the file is built and the answer
  says the name was cut, or names the part written.

*vague* and *vaguefirst* are scored as the maintainer ruled in the last record: the answer asks
which font, names the fonts, builds nothing with `--font` and asks about no other setting. A line
that asks the font and mentions page numbers is no longer counted as a second question; on the
traces of the last record that changes one run of its second set, which that record had already
passed by reading it.

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *change*, two turns | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *vague*, two turns | 2 of 3 | 1 of 1 | 1 of 1 |
| *vaguefirst* | 2 of 2 that loaded the skill | 1 of 1 | 1 of 1 |
| *checkask* | 3 of 3 | 1 of 1 | 1 of 1 |
| *checkonly* | 3 of 3 | 1 of 1 | 1 of 1 |
| *repair* | 2 of 3 | 1 of 1 | 1 of 1 |
| *fontlong* | 2 of 3 | 1 of 1 | 1 of 1 |

**Eighteen of eighteen files byte for byte what was asked. No run of *checkask* or *checkonly*
ran `build`, and no run of *checkonly* ran `repair`. In the runs of *vague* and *vaguefirst* that
loaded the skill, none chose a font.** The 48 runs cost US$4.00.

## The misses

- ***vague*, once, Haiku asked where the page numbers go**, after asking the font as a list.
  The same miss as in the last record's first set.
- **One *vaguefirst* run never loaded the skill**, as in the last record: the request names a .md
  file and neither Word nor .docx, and Haiku asked whether to make a .docx at all, and which font,
  size and page number place. The maintainer ruled in the last record that this is the
  description's reach, and it is again left out of the cell.
- ***repair*, once, Haiku asked whether to write over the file** and passed on neither the font
  `repair` chose nor that page breaks may move. It had first given `repair` the file to repair as
  its output, which `repair` refused. The same miss as one run of the last record: two runs of six
  across the two.
- ***fontlong*, once, Haiku read the three fonts `references/settings.md` names as the only ones
  allowed**, said the one asked for was not among them, and asked which of the three to use. No
  file was built and no font was chosen for the user; but the page says those are the fonts known
  to carry Thai, not the only ones a build takes.
- **The name written ends in a space.** The first 31 characters of the name asked for are
  "TH Sarabun New Extra Condensed ", and that is what the file names and the warning quotes. The
  answers that named it in their own words wrote it without the space. Sonnet said the name was 31
  characters long; it is 38. Opus added that "Regular" is likely a weight and not part of the
  font's name.
