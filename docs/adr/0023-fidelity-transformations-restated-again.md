# 0023 — Fix rendering with format attributes, never by changing content (restated with captions)

- Status: accepted
- Decided: 2026-09-16
- Supersedes: 0016

## Where it came from

0016 closed the list of transformations between the Markdown's text and the document's.
0021 then made a `Table:` or `Figure:` paragraph a caption, whose document text begins
with a label and a number the Markdown does not hold, and gave some comments a meaning.
0021 said so, but the closed list lived in 0016. The maintainer asked for it to be
restated in full here, so the list stays closed in one place.

## Decision

Display problems are fixed with format attributes and document settings only. The text
the Markdown renders — as this parser reads it, held to the reference implementations by
0015 — equals, character for character after NFC normalisation, the text of the document
and its footnotes, with exactly these transformations:

1. **Soft line breaks.** A soft line break with no rendered text before or after it in its
   paragraph becomes nothing, and so does one between two Thai characters. Any other
   becomes one space. The neighbour is the adjacent text (empty text is skipped); an
   image, a hard break or another soft break is not a Thai character.
2. **Task markers.** `[ ]` and `[x]`, with the spaces after them, become ☐ (U+2610) or ☑
   (U+2611) and one space.
3. **HTML comments** are removed. The region and list comments of 0021 leave no text:
   sections and fields, which the comparison does not read as text.
4. **Image alt text** goes to the drawing's `descr`, not into the body.
5. **Captions.** In a caption paragraph of 0021, `Table:` or `Figure:` and the spaces and
   tabs after it are removed, and the paragraph reads: the label, one space, the number,
   then — when text remains — one space and that text. The number is the one 0021 counts:
   chapter or appendix number and `-` in those regions, then the count; the build writes
   it as the fields' results and computes it again from the Markdown to compare.

A tab is text, written as `<w:tab/>`; the one tab that separates a footnote's number from
its body is layout. Numbers Word generates — list, heading, chapter, appendix, page and
footnote numbers — are formatting, not text. Header and footer text comes from the build's
flags, not the Markdown, and is outside this comparison; the checker still reads it.

No invisible character is ever added: no U+200B, U+200C, U+200D, U+2060 or U+FEFF. The
build checks all of this on every run and fails if it does not hold.

Left out on purpose, as in 0005 and 0016: zero-width spaces, or any other character, to
steer Thai line breaking. Breaking Thai lines is left to the application's dictionary,
reached through 0004.

## Why

The reasons of 0005 and 0016 stand: an invisible character is a change a proofreader
cannot see [S2], and CommonMark lets a soft break render as a space [S8] where Thai puts
none between words. A caption's label and number are what the author asked for with
`Table:` and `Figure:`, as a heading's `#` asks for a heading; writing the rule down, with
the number computed on both sides, keeps the list closed, so a machine still decides
fidelity.

## Expires when

A target application cannot break Thai lines from attributes alone and the maintainer
accepts a content change for it, or a new construct adds text the Markdown does not hold
— as a new record.
