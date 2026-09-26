# 2026-09-26 — model equivalence on the SKILL.md of 0.2.2

What this proves: the SKILL.md changed for 0.2.2 still leads three models to the file each request
asks for, byte for byte, on the four requests of
[the run on v0.2.1](2026-09-26-model-equivalence-on-v0.2.1.md); the two misses recorded there no
longer happen in these runs; and a third, found by these runs, is answered by one more sentence.
What it does not prove: a rate. Each cell is one to three runs, a sample and not a measure.

Environment: as on v0.2.1 — Linux; Claude Code 2.1.283 headless (`claude -p`,
`--setting-sources project`, tools limited to `python3`, `node`, Read, Write, Edit, Skill, Glob).
Each case is a directory outside any repository, holding the skill packed from the branch by
`tools/package_skill.py` and unpacked into `.claude/skills/`, and the request's inputs from
`tests/fixtures/`. Models: `claude-haiku-4-5-20251001`, `claude-sonnet-5`, `claude-opus-5-5`. The
requests are the four of the v0.2.1 record, word for word. The traces are the maintainer's
working copy and are not part of the repository.

## What SKILL.md says now that it did not

- **Page numbers and heading numbers by name.** The Settings section names
  `--page-numbers` (top right), `--page-numbers top-center`, `--page-numbers bottom-center` and
  `--heading-numbers`, and says to read `references/settings.md` before using any other flag:
  "never guess a name".
- **The grill message untranslated.** Grill mode says the message goes "word for word and in the
  language they wrote it in, never translated or summarised"; and that when the answer warns the
  message was read only in part, the command runs once more on its last 20,000 characters.
- **A missing picture** (added after the eighteen runs below, for what they found): the user's
  files are never changed to get a build through, and nothing they name is made up — "a picture
  that is missing is theirs to give".

## What came back

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | 3 of 3 exact, **no refused command** | 1 of 1 | 1 of 1 |
| *change*, two turns | 3 of 3 exact (`--size 14 --page-numbers`) | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3: the skill used, the file exact | 1 of 1 | 1 of 1 |

**Eighteen of eighteen files byte for byte what was asked.** No run asked anything, and no final
file carries a flag nobody asked for. The runs cost US$2.10 together.

- **Haiku no longer invents a flag.** On v0.2.1 every Haiku *thesis* run reached the file after one
  or two refused commands (`--footer-page-number`, `footer-center`). Here none was refused, and
  none of the three opened `references/settings.md`: the names in SKILL.md were enough.
- **The grill command was given the message.** It ran in nine runs of eighteen, none of whose
  messages holds the phrase, and answered `build` each time. Every message it was given was the
  user's own. One run put the skill's name in front of it and one added the argument it was
  invoked with, both as SKILL.md says. None was translated or summarised.

## A third miss, found by these runs

The first batch was set up without `pixel.png`, the picture `sample.md` names, so each *sample*,
*change* and *trigger* build stopped with `image 'pixel.png': No such file or directory`. Those
twelve runs are not counted above; they were run again with the picture. But what the models did
with the missing picture is a finding of its own:

| model | runs | told the user the line | deleted the picture's line from the user's Markdown | made up a picture |
|---|---|---|---|---|
| Haiku | 7 | 3 | 2 | 2 |
| Sonnet | 3 | 3 | 0 | 0 |
| Opus | 3 | 3 | 0 | 0 |

SKILL.md already said to tell the user the line and change a file they gave only as they say.
Haiku did otherwise in four runs of seven: it wrote `sample.md` without the image, or wrote a
`pixel.png` of its own. The sentence above was added, and the case run again on it: `sample.md`
without its picture, the *sample* request, Haiku three times and Sonnet once. All four told the
user the line (63) and what was missing; none changed `sample.md`, wrote a picture or left a
`.docx`. Four runs cost US$0.25.
