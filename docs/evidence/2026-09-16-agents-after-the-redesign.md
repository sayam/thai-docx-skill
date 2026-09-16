# 2026-09-16 — agents after the redesign: the smaller SKILL.md, the settings reference, and grill from a profile

What this proves: with SKILL.md cut to 6.8 KB and the settings, Markdown, finding codes and
sandbox moved into `references/` (ADR 0028), Claude Code agents given only the downloaded
skill still build the golden from the sample on three models and find flags they do not know
in `references/settings.md`; and the grill flow of ADR 0029 — start from a profile, answer,
save as another — runs end to end on Haiku and Sonnet. It also records what went around the
grill guard of ADR 0026, what changed because of it, and what is still open.

Environment: Linux, Claude Code 2.1.273 headless (`claude -p`, project settings only, tools
limited to `python3`, `node`, Read, Write, Edit, Skill, Glob), the harness of 2026-09-15
(`run_case.sh`, `run_two_turns.sh`), each case a directory outside any repository with the
archive from `tools/package_skill.py` unpacked into `.claude/skills/`. Start profiles were
saved in the case's project directory; profiles the runs saved in the maintainer's home were
deleted after each round. Content synthetic. Total cost 2.57 USD (1.67 + 0.63 + 0.27).

## Round 9 — the redesigned SKILL.md, grill still reading `interview.md`

| case | model | result |
|---|---|---|
| `sample.md` → `output.docx`, Thai request | Haiku 4.5, Sonnet 5, Opus 5 | all three `f176d9ac…`, the golden `sample-default.docx`; Haiku and Sonnet reported in Thai, **Opus in English** |
| passport guide, no grill | Haiku | built at once |
| settings named in Thai: 14 pt, Letter, 1 in margins, 0.5 in indent, 1.5 spacing, auto table widths | Haiku | first run with invented flags (`--font-size`, `--paper-size`), refused (exit 2); read `references/settings.md`; rebuilt with `--size 14 --paper letter --margins 1,1,1,1 --indent 0.5 --line-spacing 1.5 --table-widths auto`, reported correctly |
| `thai-docx grill …`, then `4b 7b ที่เหลือใช้ค่าเดิม` | Haiku | **passed `grill --said` the message with "thai-docx grill" cut off**; the script answered `build`; built with no questions, then did not understand the answers |
| thesis draft (as rounds 6–8) | Sonnet | `--page-numbers` only; regions, captions and lists right; text unchanged (diff checked by the agent); no warnings |
| thesis draft | Haiku (run 1) | built; **added `--heading-numbers`**, not asked |
| thesis draft | Haiku (run 2) | **added `--front-page-numbers lower-roman`**, not asked; stopped at the draft's missing images |
| notice: heading styles, bottom-centre Thai page numbers, F14 | Haiku | **invoked the skill with `grill` itself and asked the nine questions straight from `references/interview.md`, never running the command** |

## What changed after round 9

- The questions left `references/interview.md`: they come only in the grill command's JSON,
  and a test asserts the file holds none of them (ADR 0029; lesson L-0014).
- SKILL.md: give the script the user's message "all of it, word for word, the skill's name and
  anything said to the skill included".

## Round 10 — grill from the JSON, and from a profile

| case | model | result |
|---|---|---|
| `thai-docx grill …`, then `4b 7b …` | Haiku (run 1) | message passed whole; questions asked from the JSON; **in the second turn said which settings it would use and ended without building** |
| the same | Haiku (run 2) | message whole; asked; built with `--align thai --page-numbers top-right` |
| notice (no grill) | Haiku (run 1) | invoked the skill with `grill` itself again, **but ran the command on the message, got `build`, and asked nothing**; front matter and `--paper f14 --page-numbers bottom-center --thai-digits` right |
| notice (no grill) | Haiku (run 2) | built at once after two refused guesses at flags |
| `thai-docx grill from thesis save to thesis-v2 …`, then `2b 6a ที่เหลือเหมือนเดิม` | Sonnet | asked the eight questions with the current choices marked "(ตอนนี้)"; then `profile save thesis-v2 --from thesis --size 14 --default toc` and `build --profile thesis-v2`; profile `{align thai, margins 1,1,1,1, size 14}`, output `d3d3733c…` |
| the same, `thesis-v1` | Haiku | **saved and built in the first turn without waiting for answers**; in the second applied them exactly as Sonnet did, same output |

## What changed after round 10

`references/interview.md`: "Ask once, and stop there: save nothing and build nothing until the
user has answered — a start profile is not an answer", and "Do all of this in the reply that
receives the answers".

## Round 11 — the same Haiku cases, twice each

| case | result |
|---|---|
| grill from a profile, run 1 | asked and waited; `profile save thesis-v3 --from thesis --size 14 --default toc`; built `d3d3733c…` |
| grill from a profile, run 2 | the same, `thesis-v4` |
| `thai-docx grill …`, run 1 | asked; second turn built with `--align thai --page-numbers top-right` |
| `thai-docx grill …`, run 2 | **cut the phrase off the message again**; the script answered `build`; built with defaults |

## What remains open

- **Haiku trims the phrase from the message it passes** — 2 of 7 grill runs on Haiku across
  rounds 9–11 (none on Sonnet). The script cannot see words it is not given; the SKILL.md
  sentence lowered the rate and did not close it (L-0008). A guard that does not depend on the
  agent copying the message needs the client to hand it over (ADR 0026, "Expires when").
- Haiku still adds thesis flags nobody asked for (`--heading-numbers`, `--front-page-numbers`)
  on the long thesis request — the fault of round 6, 2 of 2 here.
- Opus answered a Thai request in English once.
- Not run: the question-tool form of grill (headless runs have no `AskUserQuestion`), the
  checker case, clients other than Claude Code, `PROMPT.md` in a chat app.

Harness and traces: the session scratchpad (`round-9`, `round-10`, `round-11`), copied to
`.local/work/2026-09-16-redesign/e2e/`.
