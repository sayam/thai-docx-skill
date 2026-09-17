# 2026-09-17 — `profile save` says when it replaced a profile, and what agents do with it

What this proves: `profile save`, like `profile import`, now reports `"replaced": true` and a
warning when a profile of that name was already there, the same JSON from both
implementations; and that an agent passing this on to the user is not something the words of the
skill made Haiku do.

Environment: Linux, Python 3.13, Node.js 24, Claude Code 2.1.274 headless (the harness of rounds
9–15), the archive from `tools/package_skill.py` of this change. Each case had a profile of the
same name saved first (`r16-report-N`, `--size 14`) in the maintainer's home; those files were
deleted afterwards. Content synthetic. Cost 1.44 USD (0.26, 0.21, 0.37, 0.23, 0.37).

## The script

- `tests/test_profiles.py`: a first `save` says `"replaced": false` and has no warnings; a second
  under the same name says `true` with `"warnings": ["replaced the profile house that was there
  before"]`; `import` over an existing name says the same.
- `tests/test_js_parity.py` runs `profile save` in both implementations and compares the JSON.
- Suite: 217 passed.

## The agents

The request: "บันทึกการตั้งค่าเป็นโปรไฟล์ชื่อ r16-report-N: ขนาด 15 จัดกระจายแบบไทย ใส่เลขหน้ากลางล่าง".

| round | what the skill said | case | runs | told the user it replaced one |
|---|---|---|---|---|
| 16 | `"replaced"` in the JSON; `references/profiles.md`: say so | the request alone, Haiku | 3 | 0 — one run never loaded the skill, one saved the settings to its own memory instead |
| 17 | as 16 | a Word file first, then the request (as the guide's scenario 8), Haiku | 3 | 0 of 3 (all saved, all `"replaced": true`) |
| 18 | plus a sentence in SKILL.md: when `"replaced": true`, tell the user | two turns, Haiku / Sonnet | 3 / 1 | Haiku 0 of 3; Sonnet 1 of 1 |
| 19 | the script adds a warning; no SKILL.md sentence | two turns, Haiku | 3 | 0 of 3 |
| 20 | the warning, and SKILL.md: pass on the warnings of `save` and `import` | two turns, Haiku | 3 | 0 of 3 |

## What changed

- Both implementations: `save` reports `"replaced"`, and `save` and `import` add the warning when
  it is true.
- `references/profiles.md`: when `"replaced"` is true, pass on its warning.
- The guides warn, in the command-line page and scenario 8, that `build`, `profile save` and
  `profile import` replace without asking, and say what the printed line shows. They do not
  promise that the assistant will mention it.
- SKILL.md is unchanged: neither sentence tried in rounds 18 and 20 changed what Haiku did.

## Not proved here

- Why Haiku leaves out this warning while it passes on a build's; the runs above only show that
  it does.
- Sonnet without the SKILL.md sentence, and Opus.
