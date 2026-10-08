# 2026-10-08 — model equivalence on the warnings a repair gives

What this proves: the sentence 0.3.4 changed a second time in SKILL.md — what the answer after a
repair passes on — still leads Haiku to name the new file, the font and the page breaks on the file
of [the last record](2026-10-03-model-equivalence-on-the-0.3.4-skill.md), which gives both
warnings, six runs of six. What it also shows, and does not prove: on two files that give one
warning each, Haiku said a warning `repair` had not given in one run of twelve on the old sentence
and in none on the new, and on the new it missed in two other ways the old sentence did not, once
each. Each cell is six runs, a sample and not a measure; neither sentence is shown to be better.

Environment: Claude Code 2.1.294. Model: `claude-haiku-4-5-20251001` alone; Sonnet and Opus were
not run. Each `claude -p` was capped at US$1. Every turn was billed to a Console API key (its
credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`, in all 30 turns). Each set's skill
was packed once and the same zip given to every run; the traces are the maintainer's working copy
and are not part of the repository.

## What an agent reads now that it did not

- **SKILL.md, after a repair**: "your answer names the new file, and passes on each of these
  warnings it gives: `font`, the font it chose; `layout`, that page breaks can move (say that,
  การแบ่งหน้าอาจเลื่อน in Thai, never page size or page numbers)." (V34-13)

It had said "your answer names three things: the new file; the font `repair` chose (its `font`
warning); and that page breaks can move (its `layout` warning — …)". `repair` gives `font` only
when it wrote a complex-script font where a run named none, and `layout` only when it set
compatibility mode 15; the release review of 0.3.4 found that an agent doing as it read could pass
on a warning `repair` had not given.

## The files

Every run was asked, in one turn, "ช่วย check ไฟล์ broken.docx แล้ว repair ให้ที", with one of three
files as `broken.docx`. Each file's warnings were read from `repair` in Python and in JavaScript
before the runs.

| file | what it is | `repair` warns | sha256 |
|---|---|---|---|
| *both* | `tests/fixtures/legacy-python-docx-default.docx`, as in the last record | `font`, `layout` | `fe58991a…` |
| *nolayout* | the same, its compatibility mode 14 declared as 15, nothing else touched | `font` | `81060072…` |
| *nofont* | the checker's correct document (`tests/docx_fixture.py`, `good()`), its compatibility mode 15 declared as 12 | `layout` | `6c62e75b…` |

## How it is scored

- ***both***: the rule of the last record — the new file, TH Sarabun New, and a line that names
  the page breaks and says they move.
- ***nolayout***: the new file and TH Sarabun New, and no line naming the page breaks. A line that
  names them is a warning not given.
- ***nofont***: the new file and the page breaks moving, as in *both*, and no line saying a font
  was chosen, written or set. Such a line is a warning not given.
- In every run, the file given must be left as it was.

## Two sets

**Before** (zip `656f9cc7…`, SKILL.md as on main before this change): *nolayout* and *nofont*, six
runs each. US$0.50.

**After** (zip `e8541695…`, the sentence above): *both*, *nolayout* and *nofont*, six runs each.
US$0.70. Both sets, US$1.20.

## What came back

| file | before | after |
|---|---|---|
| *both* | — | 6 of 6 |
| *nolayout* | 5 of 6; one warning not given | 4 of 6; none |
| *nofont* | 6 of 6; none | 5 of 6; none |

**Every run that repaired wrote a new file beside the one given — `broken-repaired.docx`,
`broken_repaired.docx`, `broken_fixed.docx` or `broken-fixed.docx` — and named it, and no run
touched the file given. A warning `repair` had not given was said once in twelve runs before and
in none of the eleven that repaired after. The after set missed twice in other ways, which the
before set did not in the same two files.**

## The misses

- ***nolayout*, before, once in six**: after naming TH Sarabun New, the run said
  "การแบ่งหน้าอาจเลื่อน (การแบ่งหน้าอาจเลื่อนในไฟล์ที่ซ่อมแซม)" — the layout warning, which `repair` had
  not given. The miss the review found.
- ***nolayout*, after, once in six**: the run repaired and named the new file, the findings and
  their counts, and not the font `repair` chose. Before, all six named it.
- ***nofont*, after, once in six**: the run said the compatibility mode "อาจทำให้ตำแหน่งหน้ากระดาษเลื่อนไป"
  (may move the page positions) and not that the page breaks move — the kind of miss V34-03 is
  about, which the last record's third set also showed twice in six. Before, none of six.

## Shown, not scored

- ***nolayout*, after, once in six, the run ran no command**: it loaded the skill, then asked
  for the file's path, which was in the directory it was started in. It never reached a repair,
  so the sentence had nothing to act on; it is counted as a miss of the cell.
- On *nofont*, no run of either set named TH Sarabun New or any font.
