# 2026-09-16 — grill mode taken out of the model's reading

What this proves: the interview starts only when the user's own message says so, because a
script reads the message and names the mode (gate `grill-is-the-users-word`, ADR 0026); the
request that made a model choose the interview for the user now answers `build`; and both
implementations read a message the same way (gate `javascript-matches-python`).

Environment: Linux, Python 3.13.3, pytest 8.4.2, Node.js 24.15; the working tree of this
record, not yet committed. The message used as the failing case is the synthetic thesis
request of `docs/evidence/2026-09-16-agents-with-the-grown-skill.md`, not a user's text.

## 1. What went wrong, and what changed

The agent runs of 2026-09-16 found Claude Haiku 4.5 invoking the skill with `grill` itself
on one long Thai request in four — a request that listed eight settings it wanted — and
asking the nine questions although the user had asked for none. SKILL.md already said
"never pass `grill` yourself, and never choose this mode for them"; words lowered the rate
and did not close the path (lesson L-0008).

The decision now leaves the reading: `thai_docx grill --said "<the user's message>"` prints
`{"mode": "build"}` or `{"mode": "grill", "language": "th"|"en"}`, and SKILL.md's grill
section no longer names the phrase that turns the interview on — a test asserts that, so the
agent has nothing to judge for itself.

## 2. The tests

`tests/test_grill.py` (4) and, in `tests/test_skill_md.py`, the section and both modes run
from the unpacked download; `tests/test_js_parity.py` runs seven `grill` commands in both
implementations and compares the bytes. 192 in the suite on Python 3.13.

The request that went wrong is in `tests/test_grill.py` as `LONG_REQUEST`, asserted to be a
`build`.

## 3. Defects planted in what the tests hold

Each row: one change to `grill.py`, `js/56-grill.js`, `__main__.py` or `SKILL.md`, the
JavaScript rebuilt, the named test file run, every red test read, then the file restored and
its sha256 compared with the original.

| planted defect | red |
|---|---|
| any message may start the interview | mode and language; only the user's word; the cap |
| no message ever starts it | mode and language; only the user's word; the cap |
| the phrase is read case-sensitively | only the user's word |
| an underscore is not the name's separator | only the user's word |
| a tab between the words parts them | only the user's word |
| the word `grill` alone is enough | only the user's word |
| the message is read past its cap | the cap |
| a flag the agent invents is taken | a message the command did not see |
| Thai in the message goes unseen | mode and language |
| the command is not wired up | all three |
| SKILL.md keeps the old rule in words | SKILL.md sends the decision to the script |
| JavaScript reads the whole message | command line is the same |
| JavaScript names the language when it builds | command line is the same |

All 13 red. One more was planted and is *equivalent*, not a gap:

- **JavaScript folds case with Unicode rules** (`toLowerCase()` for the ASCII fold). The
  phrase is ASCII, and no character outside ASCII lowercases into the middle of it: the
  nearest case, `İ` (U+0130), lowercases to `i` plus a combining dot, which parts `thai`
  from `-docx` rather than joining them. `["grill", "--said", "THAİ-DOCX GRILL"]` is in the
  parity cases so the two runtimes stay together on it; both answer `build`.

## 4. Not proved here

- That a model always runs the command before asking. The command closes the path from a
  correct reading of SKILL.md to the wrong mode; a model that asks questions without running
  anything is outside what any instruction or script can hold, and is what the next agent
  campaign measures.
- The rate of the old fault after the change: the agent runs of this record's date were made
  before it, and are not repeated here.
