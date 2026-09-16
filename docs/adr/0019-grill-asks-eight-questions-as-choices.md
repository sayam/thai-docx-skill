# 0019 — Two modes: build at once with announced defaults, or nine questions as choices first (restated)

- Status: superseded
- Decided: 2026-09-15
- Supersedes: 0009
- Superseded by: 0026

## Where it came from

0009 decided the two modes and the seven grill questions. Before the first release the
maintainer compared a document built from a prompt, whose paragraphs had no first-line
indent, with the same document after indenting every paragraph by hand with Word's ruler,
and asked for the indent to be one of the grill questions — with no indent still the
default — and for the questions to be asked the way Claude Design asks them: as choices
to pick, not open questions.

A headless run of the skill on Claude Haiku 4.5 had also shown that naming grill mode in
the description made a small model choose it for the user.

## Decision

**Default mode.** Build at once, with no questions. Then tell the user, in the language
they wrote in, the settings used, and that any of them can be changed. The defaults:

- TH Sarabun New, 16 pt
- A4; margins 1.5 in left, 1 in elsewhere
- Headings as Heading 1–6; paragraphs left-aligned
- No first-line indent
- No table of contents, no page numbers
- Spelling squiggles not hidden

**Grill mode.** Only when the user's own message says `thai-docx grill`, or they type
`/thai-docx grill`. An argument the agent passes when it invokes the skill is not the
user's word. The agent asks the nine questions of `references/interview.md` —
font; size; paper and margins; alignment; first-line indent; table of contents; page
numbers; hiding spelling squiggles; keeping the answers as a profile (0024) — each with its
fixed choices, choice a the default:

- with the client's multiple-choice question tool when it has one, questions 1–4 then
  5–9;
- otherwise in one message, answered in short form such as `1a 5b`.

An unanswered question keeps its default. The answers apply to that build only.

**First-line indent.** `--indent IN`, in inches like `--margins`: the choices are none,
0.5 in, 1 in, or a value typed in. It applies to the paragraphs at the document's own top
level — not headings, list items, quotations, tables, code or footnotes — and must leave
at least one inch of text on the line. No indent writes no indent element, so documents
built without the flag keep their bytes.

Without grill mode the agent never asks. A font with no Thai glyphs is a checker warning,
never a failure.

Left out on purpose:

- Saving grill answers to a file for later builds.
- Letting the agent compose its own questions or choices — small and large models would
  offer different ones.
- Thai distributed alignment, or any indent, as a default — alignment renders differently
  across the applications in 0012, and an indent is a house style, not a Thai rule.
- Indenting in centimetres: one unit across the flags.

## Why

Questions the user did not ask for are friction, and break the build-at-once behaviour
users already expect. Fixed questions with fixed choices keep grill mode inside 0007:
same answers, same flags, same file; choices also make the answers shorter to give and
impossible to misread. An indent set in the build replaces a manual pass over every
paragraph with the ruler. TH Sarabun New is the Thai government's standard font; that it
is not installed everywhere was accepted. Squiggles stay visible by default because, with
0004 in place, correct Thai carries no false ones, and hiding them hides real typos too
[S2]; 0012 confirms this by eye.

## Expires when

Users routinely change the same default, grill answers need to survive from one build to
the next, or a target client can neither show choices nor accept short answers.
