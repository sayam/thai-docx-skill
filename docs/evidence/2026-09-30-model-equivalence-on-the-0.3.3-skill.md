# 2026-09-30 — model equivalence on the skill of 0.3.3

What this proves: the text 0.3.3 changed where an agent reads it (SKILL.md's sentence on a font
the user names, its sentence on the file `repair` writes, and two reference pages) still leads
three models to the file each request of [the last record](2026-09-30-model-equivalence-on-the-0.3.2-skill.md)
asks for; a font the user names is built as named, with no question first; and after a repair no
run puts the new file over the user's own. What it does not prove: a rate. Each cell is one to
three runs, a sample and not a measure.

Environment: as in the last record, on Claude Code 2.1.285. Models: `claude-haiku-4-5-20251001`,
`claude-sonnet-5-5` (the last record ran `claude-sonnet-5`; Sonnet's cells compare across the two
records only loosely) and `claude-opus-5-5`. Each `claude -p` was capped at US$1. Every turn was
billed to a Console API key (its credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`, in
all 63 turns of each set). The skill was packed once per set and the same zip given to every run;
the traces are the maintainer's working copy and are not part of the repository.

## What an agent reads now that it did not

- **SKILL.md, "change the font"**: "ask which, in one line — TH Sarabun New, TH SarabunPSK,
  Sarabun or any font they name. A font they name is built as named, whatever it is, and the
  build's warnings are passed on." (V33-02)
- **SKILL.md, after a repair**: "OUT.docx is theirs to keep beside the file they gave: never move,
  rename or copy it over theirs, and name it in your answer." (V33-04; added after the first set,
  below)
- **`references/limits.md` and `profiles.md`**: a font's name is written cut to 31 characters,
  less a space it is cut at, and without a space at either end (V33-01).

## The files the requests ask for

No golden has moved since 0.3.0.

| case | flags | sha256 |
|---|---|---|
| *sample*, *trigger* | none | `cc1e73ba…c350` (= `tests/golden/sample-default.docx`) |
| *thesis* | `--heading-numbers --page-numbers bottom-center` | `0b64a9d6…77d2` (= `tests/golden/thesis-text.docx`) |
| *change* | `--size 14 --page-numbers` | `be3282d3…8d82` |
| *fontother* | `--font "Angsana New"` | `fc0d003e…8ea5` (the same from both implementations) |

## Two sets

**The first set** (zip `14b1b590…`, the skill without the sentence on the file `repair` writes)
passed every case but one: Haiku's *repair*, one run of three. The two that missed had `repair`
write a new file and then moved it over the user's `broken.docx`; the harness asked leave for the
move, so it did not happen. One ended by asking whether to write over the file, passing on neither
the font nor the page breaks; the other told the user `broken.docx` was fixed and ready, which it
was not. SKILL.md said that `repair` writes a new file, and nothing of what the agent does with
it. The sentence above was added, with its test, and the whole set was run again. The first set
cost US$3.43.

**The second set** (zip `3f262d63…`, the skill as it is merged) is the result below. Fourteen of
its runs — every Sonnet case, and Opus *trigger*, *vague* and *vaguefirst* — ended unrun when the
key's credit ran out; they were run again the same evening on the same zip, and their cells are
those runs.

## What came back

The ten requests of the last record, and one new one:

- *fontother*: "สร้างไฟล์ Word จาก sample.md ใช้ฟอนต์ Angsana New ตั้งชื่อ report.docx", a font the
  user names that is not one of the three SKILL.md offers. It passes when the file is the one
  asked for, byte for byte, and no question came first.

*repair* is scored as before (the answer names the font `repair` chose and says the page breaks
may move), and each run now also shows how many of its commands put a file over `broken.docx`;
that count is shown, not scored.

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *change*, two turns | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *vague*, two turns | 2 of 3 | 1 of 1 | 1 of 1 |
| *vaguefirst* | 3 of 3, each loading the skill | 1 of 1 | 1 of 1 |
| *checkask* | 3 of 3 | 1 of 1 | 1 of 1 |
| *checkonly* | 3 of 3 | 1 of 1 | 1 of 1 |
| *repair* | 2 of 3; none put a file over `broken.docx` | 1 of 1 | 1 of 1 |
| *fontlong* | 3 of 3 | 1 of 1 | 1 of 1 |
| *fontother* | 3 of 3 exact | 1 of 1 | 1 of 1 |

**Twenty-three of twenty-three files byte for byte what was asked. No run put a file over the
user's `broken.docx`, and every *repair* run named the new file. No run asked which font when the
user had named one.** The second set cost US$3.54 (US$2.46, and US$1.08 for the fourteen runs
again); both sets, US$6.97.

## The misses

- ***repair*, once, Haiku said the compatibility mode "may change where letters and lines fall"**
  and not that page breaks may move. It named the new file and the font. The same miss as one run
  of the record of 0.3.1.
- ***vague*, once, Haiku asked where the page numbers go**, after asking the font as a list. The
  same miss as in the last two records.
