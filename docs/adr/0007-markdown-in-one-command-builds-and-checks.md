# 0007 — Markdown is the only input, and one command builds and checks

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The maintainer set three principles: the file must come out the same whichever
model runs the skill, small or large; the tokens spent on tool calls must be as
few as possible; and the output must be identical on every run, proved by
regression tests. Behind them is an observation: when each model writes its own
parser or document code, each produces a different file.

## Decision

- The agent writes the content as Markdown — from the conversation, or the
  user's own file as it is — and runs one command:
  `thai_docx build in.md out.docx [flags]`.
- The command builds, then runs the checker on its own output. A failed check
  is a non-zero exit.
- It prints one JSON line: the settings used, block counts, check results.
  Never the document's text.
- The agent tells the user, in two or three lines in the user's language, what
  was built and with which settings. The hash only on request.
- `SKILL.md` tells the agent not to read the tool's source.
- The checker also stands alone, `thai_docx check file.docx`, for a .docx from
  any generator (0006).

Left out on purpose:

- A code-level helper — python-docx or any other library — that the agent calls
  run by run. It was weighed and rejected: the agent would write new program
  code for every document, so the output would depend on the model; it needs a
  library several runtimes lack (0008); and installing it at run time breaks
  0011.
- JSON as the input format. More precise, but more tokens, and more room for a
  small model to get the structure wrong.

## Why

Markdown is what every model already writes well and cheaply. Moving every
formatting decision into one fixed program is what makes a small model's file
the same as a large one's. The specification loads a skill's files only when
needed [S3], so keeping the source unread keeps it out of context.

## Expires when

A document need arises that Markdown cannot express, and the maintainer accepts
losing the same-output guarantee for it.
