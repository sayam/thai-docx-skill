# 0002 — One public repository per skill, with the skill in `skills/thai-docx/`

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The maintainer planned to publish every skill they write under
`github.com/sayam/skills`, each named with a `-skill` suffix, and asked in the
planning conversation of 2026-09-14/15 whether that layout suits. The skill also
has to follow the Agent Skills specification and be picked up by SkillsMP.

## Decision

- This skill lives in its own public repository, `sayam/thai-docx-skill`.
  `sayam/skills`, when it exists, is a catalogue that points at each skill's
  repository; it holds no skill of its own.
- The repository name carries `-skill`; the skill does not. The skill's
  directory is `skills/thai-docx/` and its `name:` is `thai-docx`.
- Only `skills/thai-docx/` is the skill. Everything else in the repository —
  `tools/`, `docs/`, `tests/`, `.github/` — is how the skill is built and
  proved, and never ships with it.

Left out on purpose: one monorepo for all skills, and a `SKILL.md` at the
repository root.

## Why

- The specification requires `name` to match the directory that holds
  `SKILL.md` [S3]. A `SKILL.md` at the root would tie the name to whatever
  directory a reader happens to clone into, and would ship this repository's
  development tooling as part of the skill.
- verifiable-gates works at the root of a repository: one decision sequence, one
  gate registry, one set of workflows [S1]. Unrelated skills in one repository
  would share all three.
- SkillsMP indexes public GitHub repositories by itself [S5], and curated lists
  link to repositories [S6]; a repository per skill is the unit both see.
- Public is not a choice: SkillsMP reads only public repositories [S5].

## Expires when

The specification lets a skill's name differ from its directory, or
verifiable-gates supports several independent projects in one repository.
