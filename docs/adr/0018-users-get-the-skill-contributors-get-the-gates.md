# 0018 — Users download the skill alone; contributors carry the gates and are held to them at merge

- Status: accepted
- Decided: 2026-09-15

## Where it came from

Before the first push, the maintainer asked whether this repository bundles
verifiable-gates, and set a requirement: someone who takes thai-docx only to use it
should not receive verifiable-gates, while someone who forks it to develop it must
carry the gates, so that whoever makes the last change before a merge is held to the
same rules.

0002 already decided that only `skills/thai-docx/` is the skill and that nothing else
ships with it. It did not say how a user gets the skill without the rest, or what
holds a contributor to the gates.

## Decision

The line is drawn by channel, not by `git clone` against fork: a fork is a copy of
the repository [S32], and git cannot give one of them less than the other.

**What a user gets — the skill directory alone.**

- Each release attaches `thai-docx-<version>.zip`, holding `thai-docx/` and nothing
  else, built from the tag by `tools/package_skill.py`, refused unless every stated
  version is the tag, and attested (gate `release-carries-only-the-skill`).
- `.gitattributes` marks everything but the skill, `README.md`, `LICENSE`,
  `CHANGELOG.md`, `PROMPT.md` and (**later**) `PROMPT.th.md` as `export-ignore` [S33], so "Download ZIP" and a
  release's source archives, which GitHub builds with `git archive` [S34], leave the
  development files out.
- The README gives a sparse checkout of `/skills/thai-docx/` for users who want git.

**What a contributor gets — everything, and a merge that enforces it.**

- The gates, tests and records stay in the tree, so every clone and fork carries them.
- `main` is protected. For everyone, the maintainer included: changes arrive by pull
  request, and the `scans`, `commits` and `tests` checks must pass [S35]. For everyone
  else, a code owner's approval is required too; the maintainer cannot approve their own
  pull request [S37], so theirs merge on the checks alone.
- `.github/CODEOWNERS` covers every path, and names the workflow, the gate registry,
  `tools/` and `requirements/` explicitly [S36]. A required check reports success
  when its job is *skipped* [S35], so a pull request that edits the workflow could
  pass by switching a job off; the owner's review is what stops it.
- The doctor refuses a `tools/` file that differs from `tools/installed.json`, and the
  commit linter (0013) now runs in CI on every commit a push or pull request adds.
- A release is cut only from a tag that passes the gates and the suite again
  (`release-check`).

Left out on purpose:

- A second repository, or a branch without the gates as the default. A branch default
  would give forks the stripped branch, the opposite of the requirement; a second
  repository would split the ADR sequence and the gate registry 0002 keeps whole.
- A git submodule for verifiable-gates. A plain clone would still hold its pointer,
  `gates.yaml` and the workflow, and CI would need the submodule anyway.

## Why

A user runs what a client loads, and a client loads the skill directory [S3]; every
other file is weight a user did not ask for. A contributor, by contrast, is exactly
the person the gates exist for, and the only merge that can be vouched for is one the
upstream repository decides — a contributor's own copy of the rules can be edited,
the base branch's protection and code owners cannot be, from a fork [S36].

## Expires when

GitHub stops building source archives with `git archive` or honouring
`export-ignore` (checked once after the first push by downloading the ZIP); branch
protection stops treating a skipped job as passing, or loses code-owner review; or
verifiable-gates ships as a CI action that no longer needs files in the tree.
