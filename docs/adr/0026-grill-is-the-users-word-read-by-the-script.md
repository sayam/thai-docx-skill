# 0026 — Two modes, and the script decides which: grill is the user's word, read (restated)

- Status: accepted
- Decided: 2026-09-16
- Supersedes: 0019

## Where it came from

0019 set the two modes and made grill mode the user's word: "an argument the agent passes
when it invokes the skill is not the user's word." That rule was written for the agent to
read, and the agent-run evidence of 2026-09-16
(`docs/evidence/2026-09-16-agents-with-the-grown-skill.md`) shows a rule in words is not a
guard. On Claude Haiku 4.5, one long Thai request in four — one that listed eight settings
it wanted (a cover, lists, บทที่, ตารางที่ 1-1, ภาคผนวก, page numbers, no text changes) —
made the model invoke the skill with `grill` itself and ask the nine questions, although
the user had asked for none. A request that names settings reads like an invitation to ask
about them.

The maintainer decided the guard must leave the model's reading (lesson L-0003: a rule the
model can only be asked to follow is not a rule the model follows).

## Decision

**Default mode.** Build at once, with no questions. Then tell the user, in the language
they wrote in, the settings used, and that any of them can be changed. The defaults:

- TH Sarabun New, 16 pt
- A4; margins 1.5 in left, 1 in elsewhere
- Headings as Heading 1–6; paragraphs left-aligned
- No first-line indent
- No table of contents, no page numbers
- Spelling squiggles not hidden

**The mode is read, not chosen.** Before the agent asks anything, it runs

```sh
thai_docx grill --said "<the user's own message, word for word>"
```

and obeys the answer: `{"mode": "build"}` — build at once, ask nothing; `{"mode":
"grill", "language": "th"|"en"}` — ask the questions in that language. The command reads
the message and nothing else: the phrase `thai-docx grill` anywhere in it, in any case,
with `-`, `_` or a space between the two words of the name, and so `/thai-docx grill` too.
A message is read to its first 20,000 characters. Nothing else turns the interview on —
not an argument the skill was invoked with, not the shape of the request, not a model's
judgement that the user would like to be asked.

**Grill mode.** The agent asks the nine questions of `references/interview.md` — font;
size; paper and margins; alignment; first-line indent; table of contents; page numbers;
hiding spelling squiggles; keeping the answers as a profile (0024) — each with its fixed
choices, choice a the default:

- with the client's multiple-choice question tool when it has one, questions 1–4 then
  5–9;
- otherwise in one message, answered in short form such as `1a 5b`.

An unanswered question keeps its default. The answers apply to that build only.

**First-line indent.** `--indent IN`, in inches like `--margins`: the choices are none,
0.5 in, 1 in, or a value typed in. It applies to the paragraphs at the document's own top
level — not headings, list items, quotations, tables, code or footnotes — and must leave
at least one inch of text on the line. No indent writes no indent element, so documents
built without the flag keep their bytes.

A font with no Thai glyphs is a checker warning, never a failure.

Left out on purpose:

- Guessing the mode from the request — the fault this record closes.
- A second trigger word, or a trigger in Thai: one phrase, written the same way
  everywhere, is a phrase the user can be told about and the tests can hold.
- The command asking the questions itself: the questions belong where the agent reads
  them, and a script cannot run a client's question tool (0007, 0011).
- Letting the agent compose its own questions or choices — small and large models would
  offer different ones.
- Thai distributed alignment, or any indent, as a default.

## Why

The interview costs the user a round of questions they did not ask for, and 0019 could
only ask the model not to start one. Moving the decision into the script makes it the same
decision for every model: the agent may still call the command, but it cannot make the
command say `grill` without the user's own words in the message, and a fabricated message
is a different fault from a misread instruction — visible, and outside what an
instruction-following model does. The rule stays cheap: one command, run only when the
agent is about to ask something.

The command answers with data, like every other command in this skill (0007), so both
implementations give the same answer byte for byte (0008), and `tests/test_grill.py` holds
the reading — including the very request that went wrong on 2026-09-16.

## Expires when

A client can hand the skill the user's message without the agent copying it, or the
interview needs to start from something other than a phrase the user types.
