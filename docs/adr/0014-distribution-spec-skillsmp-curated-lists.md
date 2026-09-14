# 0014 — Distribution: the Agent Skills specification, SkillsMP indexing, curated lists by hand

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The maintainer required compliance with the Agent Skills specification and
listing on SkillsMP, and asked whether awesome-skills.com picks skills up on its
own or has to be asked.

## Decision

- **Format.** `skills/thai-docx/SKILL.md` follows the specification [S3]:
  - front matter: `name`, `description`, `license`, `compatibility`, and
    `metadata` with `version` and `author`;
  - `description` in English with Thai keywords, at most 1024 characters, and
    the body in English, with Thai only in examples;
  - the body under 500 lines, with detail in `references/`, one level deep;
  - `agentskills validate` from `skills-ref` [S4], pinned, runs as a gate.
- **SkillsMP.** There is nothing to submit: it indexes public repositories daily
  when they have valid front matter and the topic `claude-skills` or
  `claude-code-skill` [S5]. This repository sets `claude-skills`. A reported
  minimum of two stars is not stated by SkillsMP itself, and nothing here relies
  on it.
- **Curated lists.** awesome-skills.com is curated by hand and has no submission
  form [S6]. After v0.1.0 passes 0012, the assistant drafts a message to its
  curators and pull requests to curated GitHub lists; the maintainer sends them.
- **Web apps without skill support** get `PROMPT.md`, which carries the same
  rules as a pasteable instruction.
- **The history of the source.** `docs/handoff/` keeps the diagnosis of 2026-09-14
  verbatim [S2].

Left out on purpose: sending anything to a third party on the maintainer's
behalf.

## Why

The specification is what every client in its showcase reads, so following it
is what makes the skill portable. SkillsMP decides listing by what it finds in
the repository, so the repository has to carry everything it looks for. A
curated list decides for itself, so the honest move is to ask once the skill has
earned it.

## Expires when

SkillsMP opens submissions or changes its criteria, the specification changes
its required fields, or `skills-ref` is replaced by another validator.
