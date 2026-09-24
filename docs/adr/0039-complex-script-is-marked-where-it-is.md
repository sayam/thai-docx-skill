# 0039 — A run is marked complex script where its text is complex script, not everywhere

- Status: accepted
- Decided: 2026-09-22
- Amends: [0004](0004-thai-is-complex-script-five-causes.md) cause 2, which read *"Every run that
  holds text is marked complex script"*, and cause 4, which read *"Contiguous text with the same
  formatting is one run"*
- Extends: [0023](0023-fidelity-transformations-restated-again.md) (attributes, never the text),
  [0012](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) (five applications, Word 365 for
  Windows the reference)
- Amends: [0038](0038-the-thai-language-is-written-only-when-asked.md) (which runs say they are complex
  script; the Thai complex-script language is still written only when asked)

## Where it came from

Word 365 for Windows — the reference application — draws a red underline under **correctly spelled
English words** in every document this skill builds. It is worst in an English abstract, where
nearly every word of the paragraph is underlined
([2026-09-22 Word for Windows](../evidence/2026-09-22-word-365-windows-on-the-release-bytes.md)).
ADR 0012 requires the reference application to pass *"no squiggles under correctly spelled words"*
with no exception, so this is a defect and not a limitation of that application.

Three measurements, each on 2026-09-22, found the cause and ruled out the alternatives.

**It is not what ADR 0038 changed.** Built from `v0.1.1` and from `main` in an incus container and
compared attribute by attribute, the English abstract's run differs in one thing:

| | `w:rPr` of the English abstract's run |
|---|---|
| v0.1.1 | `<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>` |
| main | `<w:cs/><w:lang w:val="en-US"/>` |

`<w:cs/>` is in both. The underline is in both. Dropping `w:bidi` neither caused it nor cured it.

**It is the package, and an attribute reaches it.** The maintainer typed `(Test Add Text)` into the
middle of that same English paragraph in Word. The typed words carry no underline; the words the
build wrote, on the same line, do. Same machine, same document, same paragraph, same language — the
only difference is which run properties the text carries. Word writes no `<w:cs/>` when a person
types Latin text; this build writes it on every run.

**`<w:cs/>` on a Latin-only run is what does it.** The element means *this run is complex script*.
Word then proofs even a Latin-only run with the complex-script language rather than with
`w:lang w:val`, and no complex-script language spells English.

## What Word itself writes

A document typed in Word 365 for Windows by the maintainer — five paragraphs covering Thai alone,
English alone, Thai and English mixed, punctuation between the two, and Arabic digits among Thai —
was read attribute by attribute
([record](../evidence/2026-09-22-what-word-writes-when-a-person-types.md)). **It carries no red
underline anywhere**, and that is the state this record aims at. It does this by:

1. declaring the languages once, in `docDefaults` and `w:themeFontLang`, and writing **no `w:lang`
   on any run** — 0 of them in the whole file;
2. putting **no `<w:cs/>` in `docDefaults`**;
3. splitting runs at every boundary between complex script and not, over and above the splits that
   formatting already forces;
4. writing `<w:cs/>` on the complex-script runs and **nothing at all** on the others — not
   `<w:cs w:val="0"/>`;
5. treating Arabic digits and ASCII punctuation as not complex script — `กลุ่มตัวอย่างจำนวน 120 ฉบับ`
   becomes five runs, and `120 ` carries no `<w:cs/>`;
6. giving a neutral character the script of the strong character before it — the space after `ผสม`
   carries `<w:cs/>`, the space after `Word` does not;
7. writing `<w:b/>` **and** `<w:bCs/>` on a bold run whichever script it is, so that dropping
   `<w:cs/>` costs a Latin run nothing.

## Decision

**Cause 2 of ADR 0004 now reads: a run whose text contains complex-script characters carries
`<w:cs/>`; a run whose text contains none does not.**

The build follows the seven rules above, which are Word's own, with one exception set out below.

- **Runs are split at script boundaries**, in addition to the splits formatting already forces.
  **Cause 4 of ADR 0004 is amended to match**: contiguous text with the same formatting *and the
  same script* is one run. What cause 4 guards against is a run boundary inside a word, and a
  script boundary never falls inside one — Thai words are wholly Thai. Pieces that end up adjacent
  with identical run properties are merged back into one run, so the checker's own reading of
  cause 4 keeps its meaning.
- **`<w:cs/>` is written on complex-script runs only**, by omission elsewhere, never by
  `<w:cs w:val="0"/>`.
- **Nothing in the inheritance chain carries `<w:cs/>` any more** — not `docDefaults`, not a
  style — so omission on a run means off. `w:cs` is not a toggle like `w:b`; it inherits straight
  down, and a run that omits it takes whatever the chain says. Leaving it in the `Normal` style
  would make the whole change invisible.
- **Arabic digits and ASCII punctuation are not complex script.** A neutral character takes the
  script of the strong character before it.
- **`w:b` and `w:bCs` are still written together**, as are `w:i`/`w:iCs` and `w:sz`/`w:szCs`, so
  cause 5 of ADR 0004 is untouched.
- **No run declares the Latin language any more.** Word writes no `w:lang` on a run at all — zero
  occurrences in the document the maintainer typed — and `docDefaults` already declares
  `w:val="en-US" w:eastAsia="en-US"`, so a run repeating it says nothing new at 28 characters a
  time. `--thai-language` is the one thing a run still says about language, because nothing else
  can say it: `w:bidi="th-TH"` may not go in `docDefaults` (below), and it is written as
  `<w:lang w:bidi="th-TH"/>` **on the marked runs only** — a run that holds no complex script has
  no complex-script language to name. Where the flag once wrote it on all 497 runs of
  `sample-text`, it now writes it on 308. This is decided on its own evidence
  rather than carried along by the `<w:cs/>` rule. A file made by hand while this was being
  investigated counted 3,135 words in Word where the control counted 3,177, which looked like a
  visible effect with no explanation and was written down as one. **It did not survive the
  release bytes**: the built `sample-text`, which carries no `w:lang` on any of its 705 runs,
  counts 3,177 in Word 365 for Windows, exactly as before (2026-09-23,
  `.local/work/2026-09-22-release-check-on-0039-bytes/RESULTS-word365_windows.md`). Underlining is
  identical either way, measured both ways in the reference application.

**The exception: `w:bidi="th-TH"` still never goes in `docDefaults`.** Five documents opened in
WPS Writer on 2026-09-22 ([record](../evidence/2026-09-22-where-wps-trips-over-the-thai-language.md))
settle where that application trips:

| where `w:bidi="th-TH"` is | SARA AM in WPS |
|---|---|
| nowhere (the control) | correct |
| **`docDefaults`** | **wrong** |
| `w:themeFontLang` | correct |
| both | **wrong** |
| every run (the control for the known fault) | **wrong** |

Both controls behaved, so the middle rows are trustworthy. ADR 0038 said WPS trips over the
attribute *"on a run, in a style, or in the document's defaults"*; this refines it: **`w:themeFontLang`
alone does not trip it.** Word 365 for Windows opened the `w:themeFontLang` document with nothing
amiss.

Whether writing it there is worth anything is not yet known — it would matter only on a machine
whose complex-script language is not Thai, which nobody has tested. **Until that is measured the
build does not write it**, and ADR 0038's default stands unchanged.

**The uniform marking stays available, as `--force-cs-whole-doc`.** Taking `<w:cs/>` off a Latin
run lets Word use the font the run actually names in `w:ascii`, and eleven runs in the fixtures name
`Consolas` for code spans — so code, which has rendered in TH Sarabun New in every release so far
because `<w:cs/>` overrode it, now renders in Consolas. That is what Word does with the same
attributes, so it is the default. But a red underline does not print, and someone whose document is
finished and who wants one font on the page rather than a correct one on the screen has a real
reason to ask for the old shape. The flag writes `<w:cs/>` on every run and leaves it in
`docDefaults`, which is exactly what v0.1.1 wrote. `references/limits.md` states the exchange: one
font throughout and English underlined on screen, against Word's own rendering and no underline.

**`check` follows, in one direction only.** Finding `2` becomes *a run with complex-script text has
no `<w:cs/>`*. A Latin run that carries `<w:cs/>` is **not** a finding — that is what
`--force-cs-whole-doc` produces, and a checker that called it an error would fail the documents this
project itself offers to build.

**`repair` carries the same flag, and its default matches the build's.** Without the flag it marks
the runs that hold complex-script text and takes the marker off the ones that do not; with it, it
marks every run, which is what it has always done. A file it did not write carries no record of
which shape its author intended, so the flag is how the author says. It still changes no text
(0023).

**Repair also splits the runs that hold both scripts**, which is new. Until now it has only ever
rewritten run properties in place, editing each part as bytes rather than re-serialising a tree —
deliberately, because a tree would rewrite prefixes, attribute order and empty-element spelling
across the whole part, and ADR 0037 permits only the attributes it names. Marking fewer runs fits
that design exactly; splitting one does not, so the question was whether to stop short.

Measurement settled it. In `sample-text`, the English that a reader sees is not mostly in
Latin-only runs: **462 Latin letters sit in runs that are Latin only, and 924 sit in runs that hold
Thai as well** — and the 462 are almost entirely the English abstract, which is one run of its own.
A repair that only cleared the marker from Latin-only runs would therefore reach about a third of
the English in a bilingual document and leave the rest underlined. The flag would mean almost
nothing.

So repair splices a mixed run into several, in bytes, at the same script boundaries the build uses,
and touches nothing else in the part. That is not the re-serialisation ADR 0037 forbids, and the
technique was measured on 2026-09-22: the parsed text of every part came back **identical character
for character**, and Word 365 for Windows opened the result with no Repair dialog. The extension of
repair's contract is stated in `references/limits.md` beside it.

The fixtures cannot test any of this as they stand. `legacy-python-docx-default.docx` has four runs
and `legacy-helper-2026-09-14.docx` has three, and **both are Thai with no Latin letter anywhere**,
so neither can show the defect or its repair. A fixture with Thai and English in one run comes with
this change.

## What the reference application then showed

Recorded in full in
[2026-09-22 marking only what is complex script](../evidence/2026-09-22-marking-only-what-is-complex-script.md).
The rules above were applied to `sample-text` by editing the XML of a built document — runs split,
`<w:cs/>` written only on complex-script runs, and the marker taken out of `docDefaults` **and out
of the `Normal` style**, which is the step that makes the rest work at all. Word 365 for Windows
opened it with no Repair dialog and:

- **no red underline anywhere in the English abstract**, where nearly every word had been underlined;
- **no red underline on the `คำสำคัญ:` line**, whose Thai and English sit in one run in the original
  — the case no paragraph-level fix could reach;
- **no red underline under Thai**, SARA AM in place, status bar still Thai;
- **24 pages, the same as the unedited control.** Splitting runs cost no layout at all.

WPS Writer opened the same file with SARA AM correct throughout. It showed 21 pages for the control
against 29 for the split arms, which Word does not reproduce on the same bytes; that difference is
recorded as WPS's own and is not treated as a cost here.

One difference in these files had no explanation: with `w:lang` dropped from runs, Word counted
3,135 words where the control counted 3,177, on text that did not change by one character. It was
written down rather than waved away — and then it did not reproduce. The built documents count
3,177, so whatever produced the difference belongs to the hand-made file and not to the shape this
record decides. A measurement that holds only in the probe is a property of the probe.

## What this costs

**Every document's bytes change. In bytes the change pays for itself.** Measured, not estimated,
by applying the rules to the release fixtures and counting `word/document.xml`:

| document | before | splitting alone | splitting **and** dropping run `w:lang` |
|---|---|---|---|
| `sample-text` | 114,705 | 128,249 · +11.8% | 112,678 · **−1.8%** |
| `sample-options` | 126,962 | 141,654 · +11.6% | 125,278 · **−1.3%** |
| `sample-basic` | 13,126 | 14,656 · +11.7% | 12,609 · **−3.9%** |

Splitting is dear — each piece carries a copy of its run properties, and `document.xml` of
`sample-text` goes from 477 runs with text to 685 pieces. But the silence about `w:lang` more than
pays it back: `<w:lang w:val="en-US"/>` is 28 characters on every run for something `docDefaults`
already declares, and dropping it saves more than the splitting costs. **Adopting the rules together leaves all three fixtures smaller
than before.** Both rules are adopted, so **every document this project writes gets slightly
smaller**, and the cost line in `references/limits.md` is about the word count, not about bytes.
An earlier estimate of +4% to +8.5% was made by counting transitions rather than by building the
files, and was wrong in both its size and its ordering; these numbers, measured on files that were
built and opened, replace it.

**The five-application check starts again.** Word for macOS and Word 365 for Windows had already
been read on the previous bytes; both results are spent.

## Why not the alternatives

**Leave it, and record it as a limitation.** `docs/rules.md` allows a deviation only when *"the
cause is in that application and our attributes cannot reach it"*. Here the cause is in the package
and an attribute reaches it. The same page closes the door from the other side too: a deviation is
unacceptable *"when the reference application fails"*, and the application failing is Word 365 for
Windows. The rules are written that way precisely to stop a defect being renamed.

**Fix it at paragraph level instead of run level** — drop `<w:cs/>` only where a whole paragraph is
free of Thai. Simpler, and mixed paragraphs would behave exactly as today. But the English abstract
of the fixtures ends with a Thai sentence on purpose, so the paragraph that showed the fault is a
mixed one and would not be fixed. The maintainer's rule is that a document this skill builds must
look like one typed in Word, and Word splits inside the paragraph.

**Write `<w:cs w:val="0"/>` on the Latin runs and keep `docDefaults` as it is.** Word does not do
this, and it adds ten bytes per run where omission saves seven.

**Ship it in v0.3.0 and tag v0.2.0 with the defect recorded.** Considered and rejected by the
maintainer on the same day the cause became known: *"if it must be fixed properly"*. A release that
fails the reference application's own checklist is not one this project's rules will tag.

## Expires when

Word changes how it itemises script runs, or a measurement shows an application that needs
`<w:cs/>` on runs that hold no complex script — in which case this record is replaced, not widened.
