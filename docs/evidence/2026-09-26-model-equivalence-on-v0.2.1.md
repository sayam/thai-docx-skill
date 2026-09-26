# 2026-09-26 — model equivalence on v0.2.1

What this proves: three models, given only the released v0.2.1 archive, each build the file a
request asks for, byte for byte. That holds for four requests: the two v0.2.0 was measured on; a
change made in a second turn, which the rewritten SKILL.md sentence on the last build's flags is
for; and a request that says neither "docx" nor "Word", which is what the skill's description has
to catch. What it does not prove: a rate. Each cell is one to three runs, a sample and not a
measure, and the trigger request is one phrasing of many.

Environment: Linux; Claude Code 2.1.283 headless (`claude -p`, `--setting-sources project`, tools
limited to `python3`, `node`, Read, Write, Edit, Skill, Glob). Each case is a directory outside any
repository, holding `thai-docx-0.2.1.zip` from the release unpacked into `.claude/skills/`, and the
request's inputs from `tests/fixtures/`. Every run's commands name that copy of the skill. Models:
`claude-haiku-4-5-20251001`, `claude-sonnet-5`, `claude-opus-5-5`. The traces are the maintainer's
working copy and are not part of the repository.

## The requests, word for word

| case | the user's message | the file it must give |
|---|---|---|
| *sample* | `สร้างไฟล์ Word จาก sample.md ให้หน่อย ตั้งชื่อ sample.docx` | golden `sample-default` |
| *thesis* | `สร้างไฟล์ Word วิทยานิพนธ์จาก thesis.md ให้หน่อย มีเลขหัวข้อ และเลขหน้าอยู่กึ่งกลางด้านล่าง ตั้งชื่อ thesis.docx` | golden `thesis-text` (`--heading-numbers --page-numbers bottom-center`) |
| *change*, two turns | `สร้างไฟล์ Word จาก sample.md ให้หน่อย ขนาดตัวอักษร 14 ตั้งชื่อ report.docx`, then `ใส่เลขหน้าด้วย` | `--size 14 --page-numbers`, sha256 `c64e9682…` |
| *trigger* | `ช่วยทำไฟล์เวิร์ดจาก sample.md ให้หน่อย ตั้งชื่อ report.docx` | the skill used, and golden `sample-default` |

## What came back

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | 3 of 3 exact, each after wrong tries (below) | 1 of 1 | 1 of 1 |
| *change* | 3 of 3 exact: the second turn kept `--size 14` | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3: the skill used, the file exact | 1 of 1 | 1 of 1 |

**Eighteen runs, eighteen files byte for byte what was asked.** No run asked the user anything,
and no final file carries a flag nobody asked for. On 0.2.0's text, one Haiku run in five added
`--toc` unasked; none did here. The runs cost US$2.16 together.

- **A change keeps the last build's flags.** In every *change* run the second build was
  `--size 14 --page-numbers`: the size asked for in the first turn survived the second. That is
  the sentence SKILL.md gained in 0.2.1.
- **The description catches "ไฟล์เวิร์ด".** A request that says neither "docx" nor "Word" used
  the skill in six runs of six. The description is left as it is (below).
- **Haiku found the thesis flags by trying.** Each *thesis* run reached the golden, and each got
  there after one or two refused commands: an invented `--footer-page-number`, an invented
  position `footer-center`, a script named `thai_docx.py` that does not exist. One run first
  built with page numbers at the top right, a file the build accepted, and then built again over
  it. The build refused every invented flag, so no wrong file was left. Haiku had not opened
  `references/settings.md` before its first build.
- **The grill command was run in eight runs of eighteen** whose messages hold no grill phrase. It
  answered `build` each time. In one of them Haiku passed an English paraphrase of the message
  instead of the message itself, which SKILL.md says never to do. With the phrase in a message,
  a paraphrase could decide the mode wrongly. This is recorded, not fixed here: 0.2.1 is kept as
  the release of the fixes found in 0.2.0, and a change to SKILL.md waits for the next.

## E-21, the skill's description

The review of 0.2.0 asked whether the description would miss a Thai request that names no file
type. It was left until it could be measured. Measured here, the description as it stands:

> Make or check a Word .docx with Thai (ไฟล์ Word ภาษาไทย). When the user's message says
> "thai-docx grill", use this skill to ask its fixed questions first.
> https://github.com/sayam/thai-docx-skill

It caught the one phrasing tried. It stays, and `tests/test_skill_md.py` holds it to the text
measured, so a change to it is measured again before it ships.
