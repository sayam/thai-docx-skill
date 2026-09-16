# 2026-09-16 — agents with the grown skill: SKILL.md, references, and what they got wrong

What this proves: after SKILL.md gained the settings, heading styles and the thesis
structure, and two files moved to `references/` (`heading-styles.md`, `chapters.md`),
Claude Code agents given only the downloaded skill still build the golden from the sample
on three models, keep both modes, and can turn a plain thesis draft into regions, captions
and lists without changing its text. It also records three faults the runs found in the
skill's instructions, the fixes, and one fault on Haiku that remains.

Environment: Linux, Claude Code 2.1.272 headless (`claude -p`, project settings only, tools
limited to `python3`, `node`, Read, Write, Edit, Skill, Glob), the harness of 2026-09-15
(`run_case.sh`, `run_two_turns.sh`). Each case: a directory outside any repository, the
archive from `tools/package_skill.py` unpacked into `.claude/skills/`, one prompt. Content
synthetic. Traces kept by the maintainer; total cost 2.22 USD.

## 1. Round 6 — the skill as it stood

| case | model | result |
|---|---|---|
| `sample.md` → `output.docx` | Haiku 4.5, Sonnet 5, Opus 5 | all three `77d0de9a…a34ed`, the golden `sample-default.docx`; settings reported in Thai |
| passport guide, no grill | Haiku | built at once |
| `thai-docx grill …`, then `4b 7b ที่เหลือใช้ค่าเดิม` | Haiku | the eight questions as one message, then built with Thai distributed and page numbers, and said so |
| plain thesis draft (no comments, captions as `ชื่อตาราง:`), asked for cover, lists, บทที่ 1, ตารางที่ 1-1, ภาคผนวก ก ข ค, page numbers, no text changes | Sonnet | read `references/chapters.md`; all region and list comments; 17 sections; ตารางที่ 1-1 … ก-1; text unchanged line for line; **also passed `--toc`**, a second table of contents on the cover |
| the same | Haiku | the same structure and unchanged text, **but added `--front-page-numbers lower-roman --appendix-numbers upper-letters --thai-digits` and `--toc`**: captions came out ตารางที่ A-๑, against the request |
| a notice: Heading 1 dark blue centred 22 pt, Heading 2 double underline, page numbers bottom centre in Thai digits, F14 | Haiku | the front matter right from SKILL.md's example; `--thai-digits --paper f14`, **no `--page-numbers`, yet it told the user the numbers were at the bottom centre** |

## 2. The fixes, and rounds 7 and 8

- SKILL.md, step 4: read the settings from `"settings"` in the JSON, not from the request;
  if something asked for is not there, add its flag and build again.
- SKILL.md, settings: add a flag only for what the user asked for.
- `references/chapters.md`: do not add `--toc` beside `<!-- toc -->`; ก ข ค front pages,
  ภาคผนวก ก and Arabic digits are the defaults; page numbers show only with `--page-numbers`.

| round | case | model | result |
|---|---|---|---|
| 7 | the notice | Haiku | `--paper f14 --thai-digits --page-numbers bottom-center`; footer1.xml present; report matches the file |
| 7 | thesis draft | Sonnet | `--page-numbers` only; 17 sections, ก ข ค, 1-1 … ก-1, text unchanged; **ended in English** ("Build succeeded…") for a Thai request, without the settings |
| 7 | thesis draft | Haiku | no extra flags, no `--toc`; structure and text right; **no `--page-numbers`** though asked — chapters.md's page bullet read as if numbers came by themselves; the page-number sentence was added after this run |
| 8 | thesis draft | Haiku | **chose grill mode itself** (`Skill` with argument `grill`) and asked the eight questions; no file |

## 3. What remains open

- Haiku can still pass `grill` itself on a long request that names many settings — the
  fault of round 1 on 2026-09-15, which SKILL.md forbids in words. One run in four of the
  thesis prompt here; a sample, not a rate. **Closed on the same day by ADR 0026**: the mode
  is now read from the user's message by `thai_docx grill --said`, and the argument the
  skill was invoked with decides nothing
  (`docs/evidence/2026-09-16-grill-is-the-users-word.md`). The runs in this record were made
  before that change; a campaign after it is still to be run.
- Sonnet answered once in English to a Thai request, against step 4.
- The chapters page-number sentence has not had a Haiku run of its own that built a file.
- Not run: the checker case, `PROMPT.md` in a chat app, clients other than Claude Code, the
  question-tool form of grill mode.
