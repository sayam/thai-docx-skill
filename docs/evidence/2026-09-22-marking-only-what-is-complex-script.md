# 2026-09-22 — Marking only what is complex script: the underlines go, and nothing else moves

What this proves: a release document with
[ADR 0039](../adr/0039-complex-script-is-marked-where-it-is.md)'s rules applied to its XML was
opened in Microsoft Word 365 for Windows — the reference application of ADR 0012 — and **every red
underline under correctly spelled English was gone**, including the English that shares a run with
Thai, which is the case no paragraph-level change could have reached. Thai was untouched: no
underline, SARA AM in place, the status bar still Thai. **The page count was identical to the
control**, so splitting runs cost no layout. This is the measurement ADR 0039 rests on, and the
answer to `2026-09-22-word-365-windows-on-the-release-bytes.md` §3.

Two things changed that nobody asked for, and both are recorded in §4 rather than left to be
discovered: code spans render in the font the document has always named for them, and Word's word
count moves.

Environment: Microsoft Word 365 for Windows on `win10-work`, a QEMU/KVM virtual machine with Thai
among its languages — the same machine as `2026-09-22-word-365-windows-on-the-release-bytes.md`.
WPS Writer 11.1.0.11723 (flatpak, Kingsoft) on the maintainer's Linux machine for the second
reading. Opened by the maintainer, one file at a time, results reported before the next was opened.
Content synthetic (ADR 0025 §10): `tests/fixtures/thesis/`.

## 1. What was opened

Three documents, all made by editing the XML of `sample-text-word365_windows.docx` as built from
`main` at `e9b5c0a`. **This is not the build doing it** — the build has no such code yet — so what
is measured here is the shape, not the implementation.

| | runs that hold no Thai | runs that hold both scripts | `docDefaults` **and** the `Normal` style | `w:lang` on runs |
|---|---|---|---|---|
| **control** | untouched | untouched | keep `<w:cs/>` | kept |
| **split** | `<w:cs/>` removed | **split at script boundaries**, marked per piece | `<w:cs/>` removed from both | kept |
| **split, no run language** | `<w:cs/>` removed | split and marked per piece | `<w:cs/>` removed from both | **removed** |

Removing `<w:cs/>` from the `Normal` style matters as much as removing it from `docDefaults`.
`w:cs` is not a toggle like `w:b`; it inherits straight down, so a run that omits it takes whatever
the chain says, and nearly every paragraph here uses `Normal`.

The control is the release bytes unchanged and had to show the fault. It did.

## 2. What Word showed

| | control | split | split, no run language |
|---|---|---|---|
| Repair dialog | none | **none** | **none** |
| red underline, English abstract | nearly every word | **none** | **none** |
| red underline, the `คำสำคัญ:` line | yes | **none** | **none** |
| `Markdown`, `Python`, `JavaScript` inside Thai paragraphs | underlined | **none** | **none** |
| red underline under Thai | none | none | none |
| SARA AM | correct | correct | correct |
| status bar in Thai body text | Thai | Thai | Thai |
| **pages** | **24** | **24** | **24** |

The `คำสำคัญ:` line is the one that settles the design. Its Thai and its English —
`เอกสารภาษาไทย, Markdown, Office Open XML, การตัดบรรทัด, complex script` — sit in a single run in
the original, so nothing short of splitting that run could have separated the English from the
complex-script marker. It comes out clean.

WPS Writer opened all three without a Repair dialog and placed SARA AM correctly in every arm, so
nothing ADR 0038 protects was traded away. WPS counted 21 pages for the control and 29 for the
other two; Word counts 24 for all three on the same bytes, and `word/document.xml` has the same 426
paragraphs, 5 tables and 17 section properties in each. The difference is WPS's own and is not
treated as a cost of this change.

## 3. The first round of this measurement was discarded

An earlier pair of files, built on the same day, made Word raise *"Word found unreadable content"*
and repair three footnotes. That was a fault in the probe, not in the shape: its pattern matched a
run and its text in one expression, so the optional run-properties group backtracked across run
boundaries and swallowed the runs that hold no text, copying them once per piece —
`footnoteReference` 2 → 5, `fldChar` 9 → 19, `drawing` 4 → 8. **Everything seen in that round was
read off a document Word had already repaired, and none of it is used here.** `docs/rules.md` makes
a Repair dialog an outright failure, which is what caught it; this project's own checker had passed
the same bytes. Written up as L-0022 and L-0023 in the maintainer's ledger.

The rebuilt files were held to the source before anyone looked at them: the nine element counts
that must not change were equal to the control's, and the **parsed** text of `document.xml`,
`footnotes.xml` and `footer1.xml` matched the control character for character — 15,036, 164 and 0.

## 4. Two changes that were not the point

**Code spans render in Consolas.** Eleven runs name `w:rFonts w:ascii="Consolas" …
w:cs="TH Sarabun New"`. With `<w:cs/>` present Word takes the font from the `w:cs` slot, so code has
rendered in TH Sarabun New in every release so far; with it gone Word takes `w:ascii`, which is what
the document asked for. Word and WPS agree, so this is the rendering the attributes have always
described. Word also underlines `w:ascii` and `w:szCs`, which are not English words. The maintainer
decided on 2026-09-22 that this is the default, because it is what Word does with these attributes,
and that `--force-cs-whole-doc` will offer the old uniform look for a finished document — a red
underline does not print.

**Word counts 3,135 words instead of 3,177** when `w:lang` is off the runs. The text did not change
by one character; Word is segmenting differently for the count. The underlining is identical either
way. It is recorded because a thesis writer reads that number, and `references/limits.md` will say
so.

## 5. Not proved here

- **The build.** These files were made by editing XML after the fact. Nothing here says the builder
  produces the same bytes, in both implementations, or that the goldens and tests follow.
- **The other four applications.** Only Word 365 for Windows and WPS Writer were opened, and WPS
  cannot answer the question at all — it does not spell-check Thai.
- **`sample-options`, `sample-layout`, `sample-basic`, `sample-auto`**, and every checklist item of
  ADR 0012 other than the ones tabled above. This reading was aimed at one question.
- **Whether `repair` can reach the same result.** It edits bytes in place and has never split a
  run; the measurement that bears on it — 462 Latin letters in Latin-only runs against 924 inside
  mixed runs — is in ADR 0039, not here.

The probe files, the script that builds them and the screenshots are the maintainer's working copy
and are not part of the repository; they are kept at `.local/work/2026-09-22-cs-probe/`, with the
round-by-round reading in `README.md`.
