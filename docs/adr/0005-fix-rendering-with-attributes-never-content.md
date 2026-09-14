# 0005 — Fix rendering with format attributes, never by changing content

- Status: accepted
- Decided: 2026-09-15

## Where it came from

During the diagnosis in [S2] the question came up of inserting zero-width spaces
to control where Thai lines break. The documents in question — research,
contracts, text already proofread — had to keep their content exactly.

## Decision

Display problems are fixed with format attributes and document settings only.
The text the Markdown renders (CommonMark [S8]) equals, character for character
after NFC normalisation, the text of every `w:t` in the document and its
footnotes — with exactly these transformations and no others:

1. A soft line break between two Thai characters becomes nothing; any other
   soft line break becomes one space.
2. Task list markers `[ ]` and `[x]` become ☐ (U+2610) and ☑ (U+2611).
3. HTML comments are removed.
4. An image's alt text goes to the drawing's `descr`, not into the body.

No invisible character is ever added: no U+200B, U+200C, U+200D, U+2060 or
U+FEFF. The build checks all of this on every run and fails if it does not hold.

Left out on purpose: zero-width spaces, or any other character, to steer Thai
line breaking — even though they would control wrapping more exactly. Breaking
Thai lines is left to the application's dictionary, reached through 0004.

## Why

An invisible character is a change a proofreader cannot see, in text whose
point is that it was proofread [S2]. Transformation 1 exists because CommonMark lets
a soft break render as a line ending or a space, which a browser shows the same
way — as a space [S8]. Thai does not separate words with spaces, so a line
wrapped in the source would gain a gap its author never typed. Closing the list is what lets a machine check fidelity instead of a
person arguing about it.

## Expires when

A target application cannot break Thai lines from attributes alone and the
maintainer accepts a content change for it — as a new record.
