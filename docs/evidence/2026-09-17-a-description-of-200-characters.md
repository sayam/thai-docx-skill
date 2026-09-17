# 2026-09-17 — a description of 200 characters: what it had to keep

What this proves: SKILL.md's description can fit the Claude apps' upload, which takes 200
characters, and end with the repository's address, and still make agents given only the
downloaded skill build at once, check an existing file, leave a document with no Thai alone,
and ask the fixed questions when the user writes `thai-docx grill` — but only if the grill
sentence keeps its whole form. Two shorter forms of that sentence broke grill mode on Haiku.

Source of the limit: Claude Help Center, "Creating custom skills": description "200 characters
maximum" (read 2026-09-17). The specification allows 1024 (ADR 0014); the description was 731.

Environment: Linux, Claude Code 2.1.274 headless (`claude -p`, project settings only, tools
limited to `python3`, `node`, Read, Write, Edit, Skill, Glob), the harness of rounds 9–12; each
case a directory outside any repository holding the archive from `tools/package_skill.py`,
built from pull request #7's branch with only the description line changed. Content
synthetic. Cost 2.41 USD (rounds 13, 14, 15: 0.92, 0.57, 0.92).

Requests, as in rounds 1–12: *compose* — the passport guide as a Word file; *grill* —
`thai-docx grill ช่วยทำเอกสาร Word เรื่องกำหนดการประชุมทีมประจำเดือนให้หน่อย`, then
`4b 7b ที่เหลือใช้ค่าเดิม`; *check* — `report.docx` (`tests/fixtures/legacy-python-docx-default.docx`)
has red squiggles and odd line breaks; *English* — a packing list for a ski trip as
`packing-list.docx`, no Thai.

## The three descriptions

| | description | characters |
|---|---|---|
| A | `Thai Word .docx without squiggles or bad wrapping. Use to make or check a .docx with Thai (ไฟล์ Word ภาษาไทย). Builds at once; "thai-docx grill" asks first. https://github.com/sayam/thai-docx-skill` | 197 |
| B | `Thai Word .docx without squiggles or bad wraps. Make or check a .docx with Thai (ไฟล์ Word ภาษาไทย). If the user's message says "thai-docx grill", ask first. https://github.com/sayam/thai-docx-skill` | 198 |
| C | `Make or check a Word .docx with Thai (ไฟล์ Word ภาษาไทย). When the user's message says "thai-docx grill", use this skill to ask its fixed questions first. https://github.com/sayam/thai-docx-skill` | 195 |

C keeps the last sentence of the old description word for word, "before building" shortened
to "first".

## Round 13 — description A

| case | model | runs | result |
|---|---|---|---|
| compose | Haiku | 3 | 3 of 3 loaded the skill and built at once |
| compose | Sonnet | 1 | loaded the skill, built at once |
| check | Haiku | 2 | 2 of 2 loaded the skill, ran `check`, explained the codes |
| check | Sonnet | 1 | loaded the skill, ran `check`, explained the codes |
| English | Haiku | 2 | 2 of 2 did not load the skill (one run stopped at the harness's permission prompt for its own python-docx script) |
| grill | Haiku | 3 | **1 of 3**: two passed `grill --said` the message with `thai-docx grill` cut off; the script answered `build`; both built with no questions and did not understand `4b 7b` |
| grill | Sonnet | 1 | passed the message whole, asked, built with `--align thai --page-numbers top-right` |

## Round 14 — the old description beside B

| case | description | runs | result |
|---|---|---|---|
| grill | the old one (731 characters) | 4 | 4 of 4 passed the message whole and asked the questions; 3 built with `--align thai --page-numbers top-right`, 1 asked for the content first |
| grill | B | 4 | **0 of 4 loaded the skill on the first turn**: each asked questions of its own about the meeting; two loaded it only on the second turn and built without the answers |
| compose | B | 2 | 2 of 2 built at once |

So the fault of round 13 came from the description, not from the model on the day: the old
description, same harness and same hour, did not show it.

## Round 15 — description C

| case | model | runs | result |
|---|---|---|---|
| grill | Haiku | 4 | 4 of 4 passed the message whole, asked the questions, built with `--align thai --page-numbers top-right` |
| compose | Haiku | 2 | 2 of 2 built at once |
| check | Haiku | 2 | 2 of 2 ran `check` and explained the codes |
| English | Haiku | 1 | did not load the skill |
| grill | Sonnet | 1 | passed the message whole, asked, built with `--align thai --page-numbers top-right` |
| compose | Sonnet | 1 | built at once |

## What changed

- SKILL.md's description is C. It names what the skill does in one clause, keeps the Thai
  keywords, keeps the grill sentence whole, and ends with the repository's address as a bare
  URL, since the specification gives the field as plain text.
- `tests/test_skill_md.py` holds the description to 200 characters, to the grill sentence of
  C, and to ending with the address.

## Not proved here

- That the Claude apps accept the upload: no upload was made. The Help Center's limit is the
  only source.
- Whether the address shows as a link in any client.
- Rates: 4 runs each for B and C are a sample (L-0008). A description that names the
  applications and the Markdown step, as the old one did, was not needed by these requests;
  a request that relies on those words was not tried.
- Opus was not run.
