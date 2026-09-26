# 0012 — XML checks are the proxy; five office applications are the release oracle

- Status: accepted
- Decided: 2026-09-15

> **Not met in full for v0.2.0:** Word for macOS was not read on its bytes and LibreOffice Writer
> only in `sample-auto`; the maintainer released first and recorded the exception
> ([2026-09-24](../evidence/2026-09-24-what-v0.2.0-was-read-in.md)). The rule stands.

## Where it came from

A check on the XML can show that the causes in 0004 are absent; it cannot show
that the document looks right to the person who opens it. The maintainer will
check releases by eye, and holds the principle that small and large models must
produce the same file (0007).

## Decision

**In CI, the proxy.** Gates for the five causes (0004), schema validity,
content fidelity (0005), byte identity (0008), the script limits (0011) and
Agent Skills validation (0014).

**Before every release, the oracle.** The maintainer opens the synthetic
fixture set in Word 365 for Windows, Word for Mac, LibreOffice, Google Docs and
WPS.

- *Every application:* content complete; bold and italic render on Thai;
  bullets show as •; Thai lines break inside words, not only at spaces; the font
  is applied; tables, links and headings are correct; footnotes are numbered at
  the foot of the page; images stay within the page; ☐ and ☑ show as symbols
  (**Later (2026-09-26):** since ADR 0033, `□` and `■` in a text font, which every reader draws).
- *Word only:* no "Compatibility Mode" in the title bar; the status bar shows
  Thai; no squiggles under correctly spelled words.

Word 365 for Windows must pass every item. An application that fails because of
a limit of its own, which attributes cannot reach, gets a "known limitation"
record naming the application and version, and the release goes ahead. Such a
failure is never fixed by changing content (0005).

**Model equivalence, before every release.** Claude Haiku 4.5, Sonnet 5 and
Opus 5 each run the skill through `claude -p` on the same Markdown; the three
hashes must match. A mismatch means `SKILL.md` is unclear, not that a model
failed. Run by hand, not in CI.

**Release.** Evidence goes to `docs/evidence/`. Versions are semver, and
`metadata.version` in `SKILL.md`, the CHANGELOG and the tag agree. v0.1.0 is
tagged only after both checks pass; only then does distribution (0014) begin.

Left out on purpose:

- Rendering in CI. No application available there renders like Word, and
  LibreOffice would be a different oracle, not a cheaper Word.
- Model-equivalence runs in CI, because of their cost and the API key they need.

## Why

A gate that passes looks exactly like a gate that checks nothing until someone
measures which it is [S1]. The application is where the user meets the file, so
it is the only place the claim can be measured.

## Expires when

These applications can be driven to render and compare automatically; the
manual pass then becomes a job.
