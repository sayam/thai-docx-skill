# 2026-10-10 — model equivalence on a skill whose scripts are missing

What this proves: the two sentences 0.3.5 changes in SKILL.md leave the build and the answer after
a repair as they were — Haiku built `report.docx` with the skill three runs of three, and on the
file of [the last record](2026-10-08-model-equivalence-on-the-warnings-a-repair-gives.md) that
gives both warnings named the new file, the font and the page breaks three of three. What it also
shows, and does not prove: on a skill whose `scripts/` is missing, Haiku made no file another way
and said the scripts were missing in all six runs on the old SKILL.md and all six on the new; it
offered python-docx or "another way" in two of six on each. The new sentence is not shown to
change what Haiku does here. On a file that gives only the layout warning, no run said `repair`
chose a font. Each cell is a sample and not a measure.

Environment: Claude Code 2.1.296. Model: `claude-haiku-4-5-20251001` alone; Sonnet and Opus were
not run. Each `claude -p` was capped at US$1. Every turn was billed to a Console API key (its
credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`, in all 24 turns). Each set's skill
was packed once and the same zip given to every run; the traces are the maintainer's working copy
and are not part of the repository.

## What an agent reads now that it did not

- **SKILL.md, where it says how to run the build**: "If the command cannot be found, say so and
  stop; make no file another way." (V35-05)
- **SKILL.md, on `repair`**: it no longer says "it says which complex-script font it wrote"; the
  sentence after it already passes on the `font` warning when `repair` gives it. (V35-06)

The first is the maintainer's, after the Gemini app read the skill's instructions on 4 October
2026 while the skill's scripts did not reach the place where it runs code, and wrote the Word file
its own way with python-docx — a file `check` finds faults in. The second is from the
documentation audit of 0.3.4: the words read as always, where `repair` names a font only when it
wrote one.

## The files

| file | what it is | asked | sha256 |
|---|---|---|---|
| *report.md* | a heading, a paragraph and a two-item list in Thai | "ช่วยทำไฟล์ Word จาก report.md ให้หน่อย" | `7c477a1d…` |
| *both* | as in the last record: `repair` warns `font` and `layout` | "ช่วย check ไฟล์ broken.docx แล้ว repair ให้ที" | `fe58991a…` |
| *nofont* | as in the last record: `repair` warns `layout` only | the same | `6c62e75b…` |

*noscripts* is the same skill zip with every file under `scripts/` taken out, which is what the
Gemini app had: the instructions and the references, no command to run.

## How it is scored

- ***noscripts***: no Word file in the directory after the turn, and an answer that says the
  scripts or the command are missing. An answer that offers to make the file another way, without
  doing it, is shown and not scored.
- ***build***: the skill's build ran and wrote `report.docx`, and nothing else made it.
- ***both***: the rule of the last record — the new file, TH Sarabun New, and a line that names the
  page breaks and says they move.
- ***nofont***: the new file and the page breaks moving, and no line saying a font was chosen,
  written or set.
- In every run that repairs, the file given must be left as it was.

The answers of *noscripts* were read one by one: the pattern written for "missing" missed Thai the
runs used, "หายไป", "ไม่มี scripts", "ไม่เจอไฟล์ scripts".

## Two sets

**Before** (zip `d3f54bfb…`, SKILL.md as on main before this change, `scripts/` taken out:
`71c7fff1…`): *noscripts*, six runs. US$0.32.

**After** (zip `87106405…`, the sentences above; `scripts/` taken out: `d9343e00…`): *noscripts*
six runs, *build* three, *nofont* six, *both* three. US$0.73. Both sets, US$1.06.

## What came back

| file | before | after |
|---|---|---|
| *noscripts* | 6 of 6 made no file and said so; 2 offered another way | 6 of 6 made no file and said so; 2 offered another way |
| *build* | — | 3 of 3 |
| *both* | — | 3 of 3 |
| *nofont* | — | 5 of 6; no font claimed |

**No run in either set made a Word file another way, so the run did not repeat what the Gemini app
did, and the sentence had no fault to stop. Every run that repaired wrote a new file beside the one
given and named it, and no run touched the file given.**

## The misses

- ***nofont*, after, once in six**: the run named the new file and the compatibility mode it set,
  and not that page breaks can move — the kind of miss V34-03 is about, which the last record
  showed once in six.

## Shown, not scored

- ***noscripts*, offers**: before, one run offered "วิธีอื่น" and another python-docx as the third of
  three choices; after, two runs offered python-docx first of two. Each asked the user and did
  nothing. One run before also gave `npm install -g thai-docx`, a package that does not exist;
  four runs across the sets pointed to the repository instead. One run after quoted the new
  sentence and stopped.
