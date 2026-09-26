# 2026-09-26 — model equivalence on the SKILL.md of 0.3.0

What this proves: the SKILL.md of 0.3.0 still leads three models to the file each request asks
for, byte for byte, on the four requests of
[the run on v0.2.1](2026-09-26-model-equivalence-on-v0.2.1.md) — the bytes of 0.3.0, which differ
from 0.2.2's for every one of the three files. What it does not prove: a rate. Each cell is one to
three runs, a sample and not a measure.

Environment: as in [the record of 0.2.2](2026-09-26-model-equivalence-on-the-0.2.2-skill-md.md) —
Linux; Claude Code 2.1.283 headless (`claude -p`, `--setting-sources project`, tools limited to
`python3`, `node`, Read, Write, Edit, Skill, Glob); each case a directory outside any repository,
holding the skill packed from the branch by `tools/package_skill.py` and the request's inputs from
`tests/fixtures/`, pictures included. Models: `claude-haiku-4-5-20251001`, `claude-sonnet-5`,
`claude-opus-5-5`. The requests are the four of the v0.2.1 record, word for word. Every turn was
billed to a Console API key (its credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`).
The traces are the maintainer's working copy and are not part of the repository.

## What SKILL.md says now that it did not

- The version, `0.3.0`.
- **Complex script is more than Thai.** "A run is marked complex script only where its text is
  complex script (Thai, or Lao, Khmer, Arabic and the like)", where 0.2.2 said "only where its
  text is Thai" (B-09).

## The files the requests ask for

Built from the fixtures by the branch's own command, each is the golden of the same flags where
there is one:

| case | flags | sha256 |
|---|---|---|
| *sample*, *trigger* | none | `bab5fb7d…8cd0` (= `tests/golden/sample-default.docx`) |
| *thesis* | `--heading-numbers --page-numbers bottom-center` | `4b9f97b9…afbd` (= `tests/golden/thesis-text.docx`) |
| *change* | `--size 14 --page-numbers` | `e7aeb0f9…8df3` |

Built by 0.2.2 with the same flags, the three give the hashes the record of 0.2.2 held them to.

## What came back

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | **2 of 3** exact | 1 of 1 | 1 of 1 |
| *change*, two turns | 3 of 3 exact (`--size 14 --page-numbers`) | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3: the skill used, the file exact | 1 of 1 | 1 of 1 |

**Seventeen of eighteen files byte for byte what was asked.** No command was refused, no run
asked anything, and no final file carries a flag nobody asked for. The eighteen runs cost US$1.57.

- **The grill command was given the message.** It was called in nine runs, none of whose
  messages holds the phrase, and answered `build` in each. Two of its eleven calls did not run —
  a wrong path to the script, and a command joined to `ls`, which the harness's tool list does
  not allow — and were made again. Sonnet twice put the skill's name in front of the user's
  message, as SKILL.md allows; no run gave it a paraphrase or a translation.

## A miss: once, Haiku did not use the skill

In one *thesis* run of three, Haiku never opened the skill. It read `thesis.md` and wrote a
python-docx program of its own, which gave a `thesis.docx` 46 KB long with neither the skill's
bytes nor its Thai marking. The two other Haiku runs, and Sonnet's and Opus's, used the skill.

That program ran only because the `python3` the case was given could import python-docx: the
harness's `PATH` led to the repository's own development environment, which a user's machine need
not have. The miss is the model's choice not to use the skill, which no sentence in SKILL.md can
reach — SKILL.md is read only once the skill is chosen, and the choice rests on the description.
It is recorded here, not closed. A run of the harness on a `PATH` with nothing but the standard
library would say whether the model reaches for the skill when python-docx is not there.
