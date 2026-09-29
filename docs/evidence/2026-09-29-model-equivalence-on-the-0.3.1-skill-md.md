# 2026-09-29 — model equivalence on the SKILL.md of 0.3.1

What this proves: the SKILL.md changed by the reviews of 0.3.1 (V31-08, V31-09) still leads three
models to the file each request of [the last record](2026-09-27-model-equivalence-after-the-review-of-0.3.0.md)
asks for; a change named without a value, asked before or after a build, is answered with a
question and no font chosen; and a request to check a .docx runs `check` or `repair`, never
`build`. What it does not prove: a rate. Each cell is one to three runs, a sample and not a measure.

Environment: as in the last record, on Claude Code 2.1.284. Models: `claude-haiku-4-5-20251001`,
`claude-sonnet-5`, `claude-opus-5-5`. Each `claude -p` was capped at US$1. Every turn was billed
to a Console API key (its credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`, in all
57 turns). The traces are the maintainer's working copy and are not part of the repository.

## What SKILL.md says now that it did not

- **`"mode": "build"` asks one thing.** "build at once, asking nothing but the value of a setting
  named without one"; `grill`'s own answer says the same, where it said "ask nothing first".
- **A change before any build** starts from the defaults plus what is asked.
- **A request about a .docx the user has** goes to *Check an existing .docx*.
- **That one value only.** "Ask that one value only: a setting asked for without a choice ("add
  page numbers") takes its default, and you say which." Added after the first runs below.

## The files the requests ask for

| case | flags | sha256 |
|---|---|---|
| *sample*, *trigger* | none | `cc1e73ba…c350` (= `tests/golden/sample-default.docx`) |
| *thesis* | `--heading-numbers --page-numbers bottom-center` | `0b64a9d6…77d2` (= `tests/golden/thesis-text.docx`) |
| *change* | `--size 14 --page-numbers` | `be3282d3…8d82` |

The last record's hashes were those of its branch; the writer fixes that went into 0.3.0 after it
(`79cb527` and the two before it) moved all three. v0.3.0, `5e99864` and this branch build the
same bytes for each.

## What came back

The six requests of the last record, and two new ones:

- *vaguefirst*: "เปลี่ยนฟอนต์ แล้วใส่เลขหน้าให้ sample.md", with nothing built yet.
- *checkask*: "ช่วย check ไฟล์ broken.docx แล้ว repair ให้ที", on the same file as *repair*.
  It passes when `check` or `repair` runs and `build` does not.

*vague* and *vaguefirst* pass when the answer asks which font, names the fonts to choose from,
builds nothing with `--font`, and asks about no other setting. SKILL.md says "in one line"; the
maintainer ruled that a list of the fonts still passes, since what V31-08 is about is a font the
user never named, and that saying the default for page numbers and asking "is that all right"
is not asking about another setting.

The first 38 runs were on the SKILL.md without the last sentence above. *vague* and *vaguefirst*
of Haiku were run again, three each, on the SKILL.md that has it; the table shows that second set
for those two cells, and the first for every other.

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *change*, two turns | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *vague*, two turns | 3 of 3 (1 in one line) | 1 of 1 | 1 of 1 |
| *vaguefirst* | **2 of 3** (1 in one line) | 1 of 1 | 1 of 1 |
| *checkask* | 3 of 3 | 1 of 1 | 1 of 1 |
| *repair* | **1 of 3** | 1 of 1 | 1 of 1 |

**Eighteen of eighteen files byte for byte what was asked. In twelve Haiku runs of *vague* and
*vaguefirst*, and four of Sonnet and Opus, no run chose a font.** The 38 runs cost US$2.97, the six
again US$0.33.

## The misses

- **Haiku lists the fonts.** Of its six answers on the last SKILL.md, two asked in one line; four
  set the three fonts out as a list. Sonnet and Opus asked in one line each time; Opus twice, and
  Sonnet once, said that page numbers go top right by default.
- **Haiku asked where the page numbers go** in one run of six on the last SKILL.md,
  and in two runs of five that loaded the skill before that sentence. The sentence is kept; three
  runs do not show that it helped.
- **One *vaguefirst* run of the first set never loaded the skill.** The request names a .md file
  and neither Word nor .docx, and Haiku asked whether to make a .docx at all. The maintainer ruled
  it outside SKILL.md: it is the description's reach, not the text the skill gives.
- ***repair*, as in the last record (2 of 3 then).** Once Haiku said the lines may move but not
  the pages; once it asked whether to write over the file and passed on no warning. Not touched by
  this change; recorded, not closed.
- **Sonnet and Opus ran *vague* and *vaguefirst* on the SKILL.md without the last sentence.** The
  two texts differ in that sentence only.
