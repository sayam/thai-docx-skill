# 0016 — Fix rendering with format attributes, never by changing content (restated)

- Status: accepted
- Decided: 2026-09-15
- Supersedes: 0005

## Where it came from

0005 decided that display problems are fixed with attributes and never by
changing content, and closed the list of transformations between the Markdown's
text and the document's. Holding the parser to the reference implementations
(0015) showed that the soft-break transformation needed two more cases to be
exact, and that the task marker is taken off where GitHub takes it off. The
principle is unchanged; the list is restated here in full, so it stays closed.

## Decision

Display problems are fixed with format attributes and document settings only.
The text the Markdown renders — as this parser reads it, held to the reference
implementations by 0015 — equals, character for character after NFC normalisation,
the text of the document and its footnotes, with exactly these transformations:

1. **Soft line breaks.** A soft line break with no rendered text before or after
   it in its paragraph becomes nothing, and so does one between two Thai
   characters. Any other becomes one space. The neighbour is the adjacent text
   (empty text is skipped); an image, a hard break or another soft break is not a
   Thai character.
2. **Task markers.** `[ ]` and `[x]`, with the spaces after them, become ☐
   (U+2610) or ☑ (U+2611) and one space.
3. **HTML comments** are removed.
4. **Image alt text** goes to the drawing's `descr`, not into the body.

A tab is text, written as `<w:tab/>`; the one tab that separates a footnote's
number from its body is layout.

No invisible character is ever added: no U+200B, U+200C, U+200D, U+2060 or
U+FEFF. The build checks all of this on every run and fails if it does not hold.

Left out on purpose, as in 0005: zero-width spaces, or any other character, to
steer Thai line breaking. Breaking Thai lines is left to the application's
dictionary, reached through 0004.

## Why

The reasons of 0005 stand: an invisible character is a change a proofreader
cannot see [S2], and CommonMark lets a soft break render as a space [S8] where
Thai puts none between words. The two added cases are what the rendered page
already shows — a line break at the very end of a paragraph, next to nothing
visible, is not a space anyone reads — and writing them down keeps the list
closed, so a machine still decides fidelity.

## Expires when

A target application cannot break Thai lines from attributes alone and the
maintainer accepts a content change for it — as a new record.
