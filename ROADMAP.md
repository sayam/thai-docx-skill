# Roadmap

What the project intends to do, and not do, from September 2026 to September 2027. It is a plan,
not a promise; each item becomes a decision record when it is taken up.

## Next release: 0.2.0

Four things, decided 2026-09-18.

| | what | where it is decided | state |
|---|---|---|---|
| 1 | **Repair a `.docx` this skill did not write** — attributes only, never the text | [ADR 0032](docs/adr/0032-repair-rewrites-attributes-never-the-text.md) | done: findings 1, 2, 3, 5 and the property order, in a file about the size it was; the split word waits for v0.3 and invisible characters are never removed |
| 2 | **`gh skill install` and `npx skills add`** held by a test, and the difference between them written in the guides | below | done 2026-09-19 |
| 3 | **The attestation attached to the release as a file** | [evidence](docs/evidence/2026-09-18-the-release-carries-its-attestation.md) | done 2026-09-18 |
| 4 | **WPS Writer re-checked** after the fixes of 0.1.0, and what it still draws its own way recorded | [evidence](docs/evidence/2026-09-19-wps-writer.md) | done 2026-09-19 |

**Repair.** `thai_docx repair IN.docx OUT.docx` writes a new file, changing only what makes Thai
render wrongly: findings `1`, `2`, `3`, `5` and `order`. A word split across two runs (`4`) is
reported and waits for v0.3; invisible characters are the user's text and are never removed. The
text of the output must equal the text of the input, character for character, or nothing is written.
Everything untouched comes through byte for byte, which the packer cannot do today — it stores every
entry, and a repaired file would come back about twenty-four times larger than the one the user gave.
So the first step is a byte-preserving round trip in both implementations, and the corpus is
synthetic throughout: defects planted in this project's own goldens, and small fixtures written by
hand from what other generators do.

Why it is worth doing at all, rather than telling people to rebuild from Markdown: a file that
arrives from somewhere else carries work nobody wants to retype, and **no other tool fixes it**.
Word does not repair a file it did not type — it rewrites every run as English and still writes no
`<w:cs/>` — and neither does an assistant working inside Word
([record](docs/evidence/2026-09-18-word-does-not-repair-what-it-opens.md)).

**The installers.** Both work today. `gh skill install` takes the latest tagged release and rewrites
SKILL.md's front matter, adding its own provenance keys; `npx skills add` takes the default branch
and copies the subtree byte for byte. Both deliver the files the release archive holds — which is
now a test, along with one that the front matter survives being sorted, flattened and unquoted the
way an installer writes it. Both guides say which installer gives which version, and give `--pin`
and `gh skill preview`. What is left is the smoke run after each release, which reaches the network
and belongs to a dated record rather than to the suite.

**WPS Writer.** Re-checked on 2026-09-19 in WPS Writer 11.1.0.11723: both fixes hold — the line
before a hard break no longer spreads under `--align thai`, and a heading's number takes the
heading's own size, font and weight — and the three lists fill on open. What WPS draws its own way
is recorded as a difference: the chapter label through a legacy code page, SARA AM's placement, and
a new one, the numbering value 1 drawn as ๕ under `--thai-digits`. The check also found something
that **was** ours: the task-list boxes were written in Segoe UI Symbol, which no Linux machine has,
so they drew as nothing outside Windows. Fixed by ADR 0033 — `□` and `■` in Arial — which changes
the bytes of any document with a task list, so the five applications of ADR 0012 are due a look
before the next release.

**Two characters that look like one.** ำ typed the long way (`ํ` + `า`) and `&nbsp;` were the two
questions left over that touch the author's own text. Both are settled by
[ADR 0034](docs/adr/0034-two-characters-that-look-like-one.md) without changing a byte a document
carries: the long form gets a build warning naming its line, because no Unicode normalisation joins
the pair and joining it ourselves would be the build editing a thesis; `&nbsp;` keeps CommonMark's
reading, which the Markdown reference already states.

## Will do

**Stay correct where users open the files**

- Check every release that changes document bytes in the five office applications of ADR 0012,
  with Word 365 for Windows as the reference.
- Re-check WPS Writer after the fixes of 0.1.0 and record what it still draws its own way (0.2.0).

**Make agents follow the skill more reliably**

- Measure again, on the smallest model, whether agents pass the user's whole message to the grill
  command and add no settings nobody asked for; change the wording the agent reads when it does not.

**Reach more users**

- Try the skill in the applications the user guide lists as "not tried yet" — ChatGPT, Codex, the
  Gemini app, Copilot, Cursor — and mark each as tried or record what fails. The Claude apps were
  done on 2026-09-18, install and build.
- Keep the release archive installable by the common installers (`npx skills add`, `gh skill install`),
  held by a test from 0.2.0.
- Submit the skill to curated skill lists by hand (ADR 0014).

**Security and project health**

- Keep code scanning (CodeQL), the dependency check (OSV-Scanner) and OpenSSF Scorecard running
  in CI, and bump every pinned tool by hand.
- Keep the assurance case current, and repeat the security review each year or at a boundary
  change (the last is `docs/evidence/2026-09-18-security-review.md`).
- Hold the project's own citations: a check that no page stating a rule now points at a record
  the index marks superseded (the drift of 2026-09-18 was found by a reviewer, not by a gate).
- OpenSSF Best Practices: passing (reached 2026-09-18), then silver as far as a one-maintainer
  project can go.

**Markdown and documents** (as users ask)

- More of what theses and official documents need, each as a setting in the registry (ADR 0028) and
  in both implementations.

## Will not do

- Accept input other than Markdown, or run with dependencies at run time (ADR 0007, 0008).
- Reach the network, run other programs, or read settings from environment variables (ADR 0030).
- Change a user's wording to make a build pass (ADR 0023).
- Name or imitate a real institution's template; profiles are for users to make and share.
