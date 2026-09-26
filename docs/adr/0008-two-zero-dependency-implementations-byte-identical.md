# 0008 — Two zero-dependency implementations with byte-identical output

- Status: accepted
- Decided: 2026-09-15
- Amended by: [0040](0040-script-limits-restated-after-the-review-of-0-2-0.md) (the same bytes on the same Unicode version, not on any)

## Where it came from

The skill must run in Claude Code, in CLI agents that run scripts — Codex CLI
[S14] and Gemini CLI [S15] both discover Agent Skills — in Claude.ai and in
Claude Design, with other vendors' web apps
served by `PROMPT.md`. A survey on 2026-09-14 checked what each runtime offers.

## Decision

- Two implementations, each using nothing beyond its language: Python 3.11 or
  later with the standard library only, and one JavaScript file that runs both
  under Node.js and in a sandbox that runs async JavaScript without modules.
- The XML parts that never vary live once, in `skills/thai-docx/assets/`, and
  both use them. The JavaScript file is built with them embedded; the built
  file is committed and held equal to a fresh build.
- Python is the reference; JavaScript is ported from it and must match.
- The same Markdown, images and settings give a .docx with the same sha256 —
  whichever implementation, run, machine or model. No clock enters a zip entry
  or a document property.
- Golden files in the test suite hold both implementations to it.

Left out on purpose: Python only, JavaScript only, and python-docx.

## Why

No single language reaches every runtime:

- Claude Code requires neither Python nor Node.js [S13].
- Codex CLI also ships as a native binary [S14].
- The Claude API's code container is Python 3.11 with no network and no package
  installs [S12].
- Claude Design runs JavaScript only — from a third-party copy of its system
  prompt, not confirmed by Anthropic [S17].
- Gemini's app accepts only `.py` and `.sh` scripts [S16].
- Claude.ai offers both [S11][S18].

Byte identity is the strictest equality there is, and the cheapest to check:
one hash.

## Expires when

One language becomes available in every runtime the skill targets, or keeping
the two byte-identical costs more than the runtimes it buys.
