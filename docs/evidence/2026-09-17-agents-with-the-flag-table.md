# 2026-09-17 — agents after the flag table: the thesis request and the grill phrase on Haiku

What this proves: after two changes to what the agent reads — the optional thesis flags moved
out of the rules of `references/chapters.md` into one table keyed on the user's words, and
SKILL.md saying that a message beginning with the skill's name keeps those words — Claude
Haiku 4.5 no longer showed the two faults left open by
`2026-09-16-agents-after-the-redesign.md` on the same prompts.

Environment: Linux, Claude Code 2.1.273 headless (`claude -p`, project settings only, tools
limited to `python3`, `node`, Read, Write, Edit, Skill, Glob), the harness of rounds 9–11; each
case a directory outside any repository holding the archive from `tools/package_skill.py`
built from this change. Content synthetic. Cost 0.88 USD.

## Round 12

| case | runs | before (rounds 9–11) | this round |
|---|---|---|---|
| the thesis draft: cover, abstract and contents on their own pages, lists of tables and figures, "บทที่ 1", captions "ตารางที่ 1-1", appendices ก ข ค, page numbers, no text changes | 3 | 2 of 2 added flags nobody asked for (`--heading-numbers`; `--front-page-numbers lower-roman`) | 3 of 3 with only `--page-numbers`: no heading numbers, front pages ก ข ค, one table of contents, captions ตารางที่ 1-1, 17–18 sections, `check` clean |
| `thai-docx grill ช่วยทำเอกสาร Word …`, then `4b 7b ที่เหลือใช้ค่าเดิม` | 3 | 2 of 7 passed `grill --said` the message with the phrase cut off | 3 of 3 passed it whole, asked the questions, and built with `--align thai --page-numbers top-right` |

The draft's two images were supplied this round (rounds 6–9 left them missing, and one Haiku
run stopped on them), so every thesis run reached a build.

## What changed

- `references/chapters.md`: "The rules" describe what the Markdown does and name no optional
  flag; a new section, "Flags — only for words the user said", maps each request to its flag,
  and says a request for "บทที่ 1" needs none. Before, the rules gave
  `--front-page-numbers lower-roman` and `--heading-numbers` inline, beside the defaults.
- SKILL.md, Grill mode: "If the message begins with this skill's name and words after it, those
  words are part of the message: pass them, never only what follows them."

## Not proved here

- Rates: six runs are a sample (L-0008). The phrase was cut in 2 of 7 runs before; 0 of 3 now
  does not show it closed.
- Sonnet and Opus, which showed neither fault, were not rerun.
