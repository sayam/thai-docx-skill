# 0038 — Every run says it is complex script; only `--thai-language` says the language is Thai

- Status: accepted
- Decided: 2026-09-20
- Extends: [0004](0004-thai-is-complex-script-five-causes.md) (the five causes),
  [0005](0005-fix-rendering-with-attributes-never-content.md) and
  [0023](0023-fidelity-transformations-restated-again.md) (attributes, never the text),
  [0012](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) (five applications, Word 365 for
  Windows the reference), [0027](0027-lists-carry-entries-and-runs-name-their-font.md) (the file
  carries what an application would otherwise supply)

## Where it came from

WPS Writer has placed SARA AM (ำ) over the wrong letter in every document this skill builds since
the first release, in every weight and every font tried
([2026-09-16](../evidence/2026-09-16-office-check-five-applications.md),
[2026-09-19](../evidence/2026-09-19-wps-writer.md)). It was recorded as that application's own,
with no cause and no way in.

On 2026-09-20 the maintainer brought a file WPS itself had written, in which ำ is placed
correctly, and asked what the difference was. Seven rounds of probe documents, each changing one
thing and opened by eye in WPS Writer 11.1.0.11723 and in Word 365 for Windows, answered it
([record](../evidence/2026-09-20-sara-am-and-the-thai-language.md)):

| what the package says | WPS draws ำ |
|---|---|
| `<w:cs/>` on the run, no language anywhere | correctly |
| `w:lang w:val="en-US"` | correctly |
| `w:lang w:eastAsia="en-US"` | correctly |
| **`w:lang w:bidi="th-TH"`** — on a run, in a style, or in the document's defaults | **wrongly** |

**It is not `<w:cs/>`,** which is cause 1's fix and the reason Word draws Thai at all. It is the
one attribute that names the complex-script *language*: wherever `w:bidi="th-TH"` is in effect,
WPS misplaces every ำ that carries no other mark above it. A ำ under a tone mark (น้ำ, ป้ำ) is
drawn correctly, which is what makes it a fault in that application's own mark ordering.

## What `w:bidi="th-TH"` buys, and what it costs

**It tells Word the language of the complex-script text is Thai**, so Word proofs it as Thai on any
machine. Without it, Word falls back to the machine's own complex-script language: on a machine set
to Thai — which every machine the maintainer tested is — the text is proofed as Thai and nothing
is underlined; on a machine set to something else, Word underlines every correctly spelled Thai
word, which is the first of the five causes this skill exists to answer.

Measured on 2026-09-20, in three Windows virtual machines with Word 365 for Windows: with
`w:bidi="th-TH"` gone, Thai is drawn correctly, carries no red underline and the status bar reads
Thai, in all three. **All three have Thai among their languages**, so they say nothing about a
machine that does not.

## Decision

**Every run keeps `<w:cs/>`.** That is cause 1's fix, it is what makes Word draw Thai, and it is
not what WPS trips over.

**`w:bidi="th-TH"` is written only when `--thai-language` asks for it**, and then everywhere the
build writes a language: the document's default run properties, every style, every run, and
`w:themeFontLang` in the settings. Off by default.

**Why off by default.** The reader's machine decides the complex-script language when the document
does not, and every machine this skill is for — a Thai document, written by someone typing Thai —
has Thai among its languages. Against that, ำ misplaced in WPS Writer is wrong on the page for
every reader who opens it there, whatever their settings. The default is the one that is right on
the page.

**Why the flag exists at all.** A document that must be correct on a machine whose complex-script
language is *not* Thai — a reader abroad, a shared machine, a server that renders documents —
needs the language written in, and then it is worth what it costs. `--thai-language` is the way to
say *guarantee it everywhere*, and the pages that describe it say in the same breath that WPS
Writer will misplace ำ in that document.

**`check` follows.** Finding `2` is now the missing `<w:cs/>` alone. The absence of a Thai
complex-script language is no longer a defect in a file, because it is no longer a defect in the
files this skill writes; the checker counts the runs that carry it and says nothing about the ones
that do not.

**`repair` follows too.** It writes `<w:cs/>` as before, and writes the language only when given
`--thai-language`, reporting how many run properties it marked.

## What this gives up, plainly

**A document built without the flag relies on the reader's machine having Thai.** Where it does
not, Word underlines correctly spelled Thai words — the very symptom of cause 1 — and the answer
is to build again with `--thai-language`. `references/limits.md` says so where a user meets it,
and both guides carry the two cases side by side.

**Neither choice is right for everyone**, and this record says which way the default leans and
why, rather than pretending the question does not exist.

## Why not the alternatives

**Keep `w:bidi="th-TH"` and record the WPS difference, as before.** That was the state until
today, and it was defensible while the cause was unknown. It is not now: the cost is paid by every
WPS reader of every document, to buy a guarantee that matters only on a machine without Thai.

**Write the language in the styles but not in the runs, or the other way round.** Measured: WPS
misplaces ำ wherever the attribute is in effect. There is no half of it that is safe.

**Drop `w:lang` altogether.** `w:val="en-US"` is the Latin language and costs nothing in any
application tested; removing it would take English proofing away for no gain.

## Expires when

WPS Writer orders Thai marks correctly under a Thai complex-script language — then the flag's
cost disappears and the default should go back to writing it; **or** evidence arrives that readers
commonly meet Word on machines without Thai, in which case the default flips and the flag becomes
the way to ask for the WPS-safe document instead. Either way, this record is replaced rather than
quietly widened.
