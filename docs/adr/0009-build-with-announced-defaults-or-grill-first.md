# 0009 — Two modes: build at once with announced defaults, or interview first

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The maintainer observed that AI tools produce a Word file straight away with
their defaults, without asking, and this skill should behave the same — with an
explicit way to be interviewed first. An earlier idea, always asking the user
for a font, was dropped because it contradicted that.

## Decision

**Default mode.** Build at once, with no questions. Then tell the user the
settings used, and that any of them can be changed. The defaults:

- TH Sarabun New, 16 pt
- A4; margins 1.5 in left, 1 in elsewhere
- Headings as Heading 1–6; paragraphs left-aligned
- No table of contents, no page numbers
- Spelling squiggles not hidden

**Grill mode.** `/thai-docx grill`, or "thai-docx grill" typed in a client
without slash commands. The agent asks a fixed set of questions from
`references/interview.md`, all in one round: font; size; page and margins;
alignment (left or Thai distributed); table of contents; page numbers; hiding
spelling squiggles. An unanswered question keeps its default. The answers apply
to that build only.

Without that command the agent never asks. A font with no Thai glyphs is a
checker warning, never a failure.

Left out on purpose:

- Saving grill answers to a file for later builds.
- Letting the agent compose its own questions — small and large models would
  ask different ones.
- Thai distributed alignment as the default — it renders differently across the
  applications in 0012.

## Why

Questions the user did not ask for are friction, and break the build-at-once
behaviour users already expect. Fixed questions keep grill mode inside 0007:
same answers, same flags, same file. TH Sarabun New is the Thai government's
standard font; that it is not installed everywhere was accepted. Squiggles stay
visible by default because, with 0004 in place, correct Thai carries no false
ones, and hiding them hides real typos too [S2]; 0012 confirms this by eye.

## Expires when

Users routinely change the same default, or grill answers need to survive from
one build to the next.
