# Roadmap

What the project intends to do, and not do, from September 2026 to September 2027. It is a plan,
not a promise; each item becomes a decision record when it is taken up.

## Next release: 0.2.0

Four things, decided 2026-09-18.

| | what | where it is decided | state |
|---|---|---|---|
| 1 | **Repair a `.docx` this skill did not write** — today attributes only, never the text | [ADR 0037](docs/adr/0037-repair-renumbers-what-the-build-would-have-written.md) | done: findings 1, 2, 3, 5 and the property order, in a file about the size it was; the split word waits for v0.3 and invisible characters are never removed |
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
is recorded as a difference: SARA AM's placement. Two more read that day — the chapter label drawn
as Latin letters and the numbering value 1 drawn as ๕ — did not reproduce on 2026-09-23, on the
same bytes as before ADR 0039 and on the bytes after; what changed is not established. The check
also found something
that **was** ours: the task-list boxes were written in Segoe UI Symbol, which no Linux machine has,
so they drew as nothing outside Windows. Fixed by ADR 0033 — `□` and `■` in Arial — which changes
the bytes of any document with a task list, so the five applications of ADR 0012 are due a look
before the next release.

**SARA AM in WPS Writer, and the language the document declares.** Seven rounds of probes, opened
by eye in WPS Writer and in Word, found the one attribute behind a difference recorded since the
first release: `w:bidi="th-TH"`, the Thai complex-script language
([evidence](docs/evidence/2026-09-20-sara-am-and-the-thai-language.md)). It is now written only
when `--thai-language` asks ([ADR 0038](docs/adr/0038-the-thai-language-is-written-only-when-asked.md)),
and the default takes the language from the reader's machine. **Owed before the tag:** if it can be
found, a Windows machine with no Thai among its languages, which is the one case the default gives
up and which no machine in this round could test.

**Correctly spelled English is no longer underlined.** Every run the build wrote said it was complex
script, English included, so Word proofed English with a complex-script language. A run is now
marked where its text is complex script, in the build, the checker and `repair`
([ADR 0039](docs/adr/0039-complex-script-is-marked-where-it-is.md)); `--force-cs-whole-doc` keeps the
old shape for a finished document read in one font. It changed every document's bytes, so the five
applications were read again:

| application | on the bytes after ADR 0039 |
|---|---|
| Word 365 for Windows (the reference) | every file, and every item of `sample-auto`'s edits — passed (2026-09-23) |
| WPS Writer | every file — passed, but for SARA AM under `--thai-language`, as recorded (2026-09-23) |
| Google Docs | read (2026-09-22); its record is owed |
| Word for macOS | **owed** — read on 2026-09-22 on the bytes before |
| LibreOffice Writer | **owed** |

and Word for the web owes the double field update the section-break fix asked for.

**Repair puts a document's own numbering back.** The terms a document is handed over on are now
written down once, in `skills/thai-docx/references/limits.md`: what the skill promises, what the
reader does after opening the file, what does not renumber itself once they edit it, where the five
applications differ, and what `repair` will and will not touch. The five-application contract covers
the ready-to-use document; `--auto-numbering` is made for Word and its variant is opened there
alone. [ADR 0037](docs/adr/0037-repair-renumbers-what-the-build-would-have-written.md) decided the
next step and it is **not yet shipped**, in this order:

1. **repair reads a document's numbering kind** — automatic (`w:numPr` on headings, `SEQ`/`STYLEREF`
   captions, numbered list items) or written (numbers as text) — and says which it is. Where it is
   automatic, repair writes nothing: the assistant asks the user which the document should be.
2. **repair re-runs the written numbers** — a heading's, a caption's, an ordered list's — to the
   document's own pattern, reporting every one it changed, with the author's words still compared
   character for character.
3. **repair brings a paragraph's indent and a run's font to the document's own majority pattern**,
   not to this skill's defaults.

Until all three ship, no page may describe repair as doing any of it.

**Who counts.** The build writes every heading, list and caption number as text, in every
document, so a file reads the same in all five applications; `--auto-numbering` hands the counting
to the application for a document someone will go on editing in Word
([ADR 0036](docs/adr/0036-who-counts-is-one-switch.md)). The first application of this release's
check — Word 365 for Windows, on `sample-options` — passed every item of the look and is what
raised the question ([record](docs/evidence/2026-09-19-the-look-passes-the-edit-does-not.md)).
`sample-auto` has since passed every item in Word 365 for Windows, the edits included — a heading,
a chapter, a list item and a caption inserted, each renumbering what follows — and WPS Writer draws
and renumbers it too. What a reader does after inserting a chapter or adding a caption is in
`references/numbering.md`.

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
- Keep the project's own citations held: the gate `live-pages-cite-the-record-in-force` reads
  every live page for a citation of a record the index marks superseded (built 2026-09-19, after
  the drift of 2026-09-18 was found by a reviewer and not by a gate).
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
