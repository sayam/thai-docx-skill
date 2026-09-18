# Roadmap

What the project intends to do, and not do, from September 2026 to September 2027. It is a plan,
not a promise; each item becomes a decision record when it is taken up.

## Next release: 0.2.0

Four things, decided 2026-09-18.

| | what | where it is decided | state |
|---|---|---|---|
| 1 | **Repair a `.docx` this skill did not write** — attributes only, never the text | [ADR 0032](docs/adr/0032-repair-rewrites-attributes-never-the-text.md) | findings 1, 2, 3 and 5 are done, and a repaired file is about the size it was; the property order is next, and the split word waits for v0.3 |
| 2 | **`gh skill install` and `npx skills add`** held by a test, and the difference between them written in the guides | below | to do |
| 3 | **The attestation attached to the release as a file** | [evidence](docs/evidence/2026-09-18-the-release-carries-its-attestation.md) | done 2026-09-18 |
| 4 | **WPS Writer re-checked** after the fixes of 0.1.0, and what it still draws its own way recorded | below | to do |

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
and copies the subtree byte for byte. Both deliver the same 29 files the release archive holds. v0.2
adds a test that the subtree and the archive stay the same set of files, a test that the front
matter survives being re-serialised with sorted keys and unquoted values, and a line in both guides
saying which installer gives which version and how `--pin` asks for an exact tag.

**WPS Writer.** Two fixes landed after the last check — the line before a hard break no longer
spreads letter by letter under `--align thai`, and a heading's number takes the heading's own size,
font and weight — and nobody has opened the files in WPS since. The re-check confirms those two,
and records what WPS draws its own way (chapter numbers through a legacy code page, SARA AM
placement) as differences rather than defects, with Word 365 for Windows as the reference.

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
