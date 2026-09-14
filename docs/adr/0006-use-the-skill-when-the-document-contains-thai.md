# 0006 — Use the skill whenever the document will contain Thai, and only then

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The case that started this repository was one Markdown file converted to Word
[S2]. The maintainer set the real scope wider: any Thai or mixed Thai–English
document an AI is asked to produce, typically the conclusion of a conversation.
Claude.ai already ships a general docx skill [S18], and a broad description
would compete with it.

## Decision

- The skill is used when the document being produced will contain Thai
  characters, whatever it comes from: a conversation, a Markdown file the user
  uploaded, data.
- It is also used to check a Thai .docx someone already has. In v0.1 that is a
  report of what is wrong; repair comes in v0.2.
- It is not used for documents without Thai.

Left out on purpose: repairing existing files in v0.1. Files from other
generators vary too widely to repair safely without a test corpus of their own.

## Why

An agent chooses a skill by its description [S3]. Keeping the description to
Thai stops two docx skills from claiming the same request, and checking an
existing file is the part of repair that can be exact from the start.

## Expires when

Repair lands (a new record for v0.2), or the general docx skills in the target
clients handle Thai correctly on their own.
