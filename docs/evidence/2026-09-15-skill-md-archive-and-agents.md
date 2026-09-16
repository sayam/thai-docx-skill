# 2026-09-15 — SKILL.md, the download, and agents using the skill

What this proves: the release archive holds the skill directory and nothing else, and
the same bytes on every run; `SKILL.md` passes the Agent Skills validator and says only
what the skill does, down to the commands and snippet run as written from the archive
(gates `skill-archive-is-the-skill`, `skill-md-tells-the-truth`); a download of the
repository leaves the development files out (ADR 0018); and Claude Code agents on three
models, given only the downloaded skill, build the same file and follow the two modes of
ADR 0009.

Environment: Linux, Python 3.13, 3.12 and 3.11.16, Node.js 24.15, skills-ref 0.1.1, git 2.49,
Claude Code 2.1.272 headless (`claude -p`, project settings only, no session saved, tools
limited to `python3`, `node`, Read, Write, Edit, Skill, Glob). The tree as committed with
this record; archive sha256 `9a633b49…bad02` for the final agent runs. All content
synthetic.

## 1. The tests, and defects planted in what they hold

`tests/test_skill_md.py` (9) and `tests/test_package_skill.py` (4); 156 in the suite on
Python 3.13, 3.12 and 3.11. Each row: one change, the two files run, every red test read,
the file restored and its hash checked; control run 13 passed.

| planted defect | red |
|---|---|
| SKILL.md states 14 pt as the default size | settings table |
| SKILL.md names `--table-of-contents` | every flag named; settings table |
| SKILL.md drops the `--page-numbers` row | every flag named; settings table |
| SKILL.md names finding code `ordering` | finding codes table |
| SKILL.md gives `thai-docx.js` for `thai_docx.js` | commands run as written |
| the sandbox snippet calls `ThaiDocx.build` | no-shell snippet |
| `name: thai_docx` | validator |
| a link to `references/questions.md` | ceiling and links |
| SKILL.md says 0.1.0, the package 0.1.0-dev | one version |
| the interview drops question 7 in English | seven questions each language |
| the archive also packs `gates.yaml` | archive holds the skill only; same bytes |
| the archive dated by the clock | same bytes |
| the tag check never refuses | tag check |
| SKILL.md swaps the flags of table of contents and page numbers | settings table |
| the archive packs `__pycache__` and stray `.pyc` files | same bytes |
| the interview drops question 8 in Thai | eight questions with choices |
| the interview maps no flag for the indent question | eight questions with choices |
| Thai and English offer different indent choices | eight questions with choices |
| SKILL.md leaves `--indent` out | every flag named; settings table |

All 19 red (the earlier "drops question 7" row no longer applies to the eight-question
interview and is replaced by the question-8 row). The last two were added after an independent review found the settings
test accepted any flag that changed *something*, and the bytecode exclusion was never
exercised; both tests were tightened first. The clock row was planted with a seconds offset: two runs inside the same
two-second DOS timestamp would pack equal bytes, so that test holds a fixed date only
against a clock that moves between runs.

## 2. What a download carries, and what a fork is held to

In a throwaway clone with the working tree committed:

- `git archive HEAD` — what GitHub's source archives are built with [S34] — lists
  `CHANGELOG.md`, `LICENSE`, `README.md` and `skills/thai-docx/**` only (PROMPT.md was
  added after this listing and is not export-ignored).
- The README's sparse checkout (`--filter=blob:none --sparse`, then
  `sparse-checkout set --no-cone /skills/thai-docx/`) leaves the 15 files of the skill
  and nothing else.
- One line appended to `tools/checks/scan_adr_index.py`: `gates_doctor.py` exits 2,
  "tools/checks/scan_adr_index.py is not what was installed".
- An unsigned commit with a non-Conventional subject: `lint_commits.py --range` exits 1
  on both counts. The five commits already on `main` pass.

Not measurable before the first push: that GitHub's "Download ZIP" matches `git
archive`, and branch protection with code-owner review — both recorded as checks to do
after the push.

## 3. Agents with only the downloaded skill

Each run: an empty directory outside any repository, the archive unpacked into
`.claude/skills/`, one prompt. Traces kept by the maintainer.

**Model equivalence (ADR 0012)** — `tests/fixtures/sample.md` as `input.md`, prompt
"ช่วยทำไฟล์ Word จาก input.md ให้หน่อย ตั้งชื่อไฟล์ว่า output.docx", final SKILL.md:

| model | output.docx sha256 | cost (USD) |
|---|---|---|
| Claude Haiku 4.5 | `122e2553…aeb669c36` | 0.047 |
| Sonnet 5 | `122e2553…aeb669c36` | 0.096 |
| Opus 5 | `122e2553…aeb669c36` | 0.187 |

All three equal the committed golden `tests/golden/sample-default.docx`; each loaded the
skill, ran one build, and reported the settings in Thai.

**The two modes (ADR 0009)**, on Haiku unless named:

| round | prompt | result |
|---|---|---|
| 1 | a short Thai passport guide, no mention of grill | **wrong**: Haiku invoked the skill with the argument `grill` itself and ended with the seven questions, no file |
| 1 | Sonnet 5, the same prompt | built at once |
| 1 | `thai-docx grill …` | the seven fixed questions |
| 1 | a legacy .docx with squiggles, "what is wrong?" | ran `check`, explained codes 1, 5 and `order`, offered to rebuild |
| 2 | after the description and body said grill is the user's word only: passport guide ×3, Songkran notice, English request for a Thai menu | all built at once; the English request was answered in Thai |
| 2 | `thai-docx grill …` | **wrong**: did not load the skill, asked questions of its own |
| 3 | after the description said grill is done by this skill, and the reply follows the user's language: `thai-docx grill …` ×3 | the seven fixed questions, all three |
| 3 | passport guide ×2, English request | built at once; the English request answered in English |
| 4 | Sonnet 5, legacy .docx | ran `check`, explained the findings, offered to rebuild |
| 5 | eight questions as choices (ADR 0019), two turns: `thai-docx grill …`, then `5b ที่เหลือใช้ค่าเดิม` — Haiku and Sonnet | both asked the eight questions with their choices as one message (no question tool in headless mode; Sonnet looked for one), then built with `--indent 0.5` and reported the indent. Haiku copied internal *(type)* marks into the message — removed from the interview afterwards; Sonnet shortened some choices |

`PROMPT.md` as written, pasted with the archive into a directory with no skill installed
(Haiku): unzipped, read `SKILL.md`, wrote Markdown, built, reported the settings.

## 4. Not proved here

- Rendering in office applications (ADR 0012's release check).
- Clients other than Claude Code, and chat apps other than one simulated with Claude.
- Behaviour on a model is a sample: three to five runs per prompt, not a rate.
- The question tool path of grill mode: headless `claude -p` has no multiple-choice tool, so
  only the one-message form was run; the interactive form is for the maintainer to try.
