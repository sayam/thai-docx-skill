# 0034 — Two characters that look like one: ำ written long, and `&nbsp;`

- Status: accepted
- Decided: 2026-09-19
- Extends: [0023](0023-fidelity-transformations-restated-again.md) (attributes, never content),
  [0022](0022-markdown-accepted-restated.md) (what stops the build and what only warns)

## Where it came from

Two questions were left open by the WPS re-check and by the reading of the Markdown reference,
and they turn out to be the same question asked twice: **what does the build do about a thing the
author typed that will not look like what they meant?**

**ำ, written the long way.** `ำ` is U+0E33 SARA AM. It can also be typed as `ํ` (U+0E4D NIKHAHIT)
followed by `า` (U+0E32 SARA AA). On screen the two are usually indistinguishable. In the file they
are not the same text at all: a search for `ำ` skips the long form, a sort orders it elsewhere, and
a reader that composes marks its own way may draw it badly — WPS already misplaces even the short
form ([record](../evidence/2026-09-19-wps-writer.md)).

**`&nbsp;`.** CommonMark resolves HTML entities, so `&nbsp;` in the Markdown becomes one U+00A0 in
the document, not the seven characters typed. An author who wanted the literal text is surprised;
an author who wanted a non-breaking space got exactly what they asked for.

## What was measured, 2026-09-19

With Python's `unicodedata`:

| | decomposition | NFC joins them? | NFKC joins them? |
|---|---|---|---|
| `ำ` U+0E33 | `<compat> 0E4D 0E32` | — | — |
| `ํ` + `า` | — | **no** | **no — it goes the other way** |
| `&nbsp;` U+00A0 | `<noBreak> 0020` | — | becomes a plain space |

The direction matters and settles the case. **No Unicode normalisation composes `ํ` + `า` into
`ำ`.** NFC leaves them as two characters. NFKC does change something — it takes `ำ` *apart* into
those same two — so normalising harder would make the short form worse, not the long form better.
Anything that joined them would be a transformation this project invented: exactly what ADR 0023
forbids.

U+00A0 is likewise not one of the five invisible characters the character model of ADR 0015
refuses (U+200B, U+200C, U+200D, U+2060, U+FEFF). Those are hacks that make text lie about itself; a non-breaking space is
ordinary typography, and `check` has no finding for it.

## Decision

- **Neither is changed, and neither is refused.** The document carries the characters the author
  typed, after NFC and nothing more.
- **`ํ` immediately followed by `า` raises a build warning**, with its line number, saying that it
  looks like `ำ` but is two characters and that a search for `ำ` will not find it. Both
  implementations, one wording.
- **`&nbsp;` gets no warning.** CommonMark's answer is a correct one and the `references/markdown.md`
  entry that says so is the whole remedy. A warning on every entity would fire on `&amp;` too, in
  documents that are right.

The line between them is whether the surprise can be a defect in the finished document. A long
`ำ` can be; a non-breaking space cannot.

## Why not the alternatives

**Rewrite `ํ` + `า` as `ำ`.** It is the one thing the author did not ask for. It would also be
unreliable in the direction that matters: the sequence is legal Thai in its own right after some
consonants, and this project has no dictionary and wants none. ADR 0023 exists so the build can
never be accused of quietly editing a thesis.

**Refuse it.** A refusal has to be for something that cannot be written correctly at all. This can:
the file is valid, Word opens it, and the text reads the way it was typed. Refusing would make the
skill unusable for an author whose keyboard or source produced the long form throughout — and they
would have no way to comply except to edit text this project told them was unsupported.

**Normalise to NFKC.** It would decompose every `ำ` in the document into the long form — turning
one questionable line into all of them, and making the WPS placement problem universal.

**Warn about `&nbsp;` too.** The warning list is worth reading only while every line on it is
worth acting on. Entity resolution is CommonMark, documented, and usually intended.

## What it costs

One more warning that documents with the long form will now carry, every build. Nothing in any
document's bytes changes, so no golden and no oracle file moves.

## Expires when

Unicode gains a composition for `ํ` + `า` — which it will not, since the pair is a compatibility
decomposition and those are stable — or the project gains a text-repair mode that asks before
changing anything, where this would belong instead of in a warning.
