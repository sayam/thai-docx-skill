# 2026-09-29 — release tags are signed and cannot be moved

The review of 0.2.0 found (F-08) that the release tags were lightweight and unsigned, and that no
ruleset covered tags: anyone with write access could move `v0.2.0` to another commit and run the
release workflow again. A tag is the only thing that names the commit a release is, so this record
states what now holds it. Two of the controls are repository settings, which no test in the tree
can read. They were read on this day.

## The ruleset

`gh api repos/sayam/thai-docx-skill/rulesets/24035355`:

| field | value |
|---|---|
| name | `release-tags` |
| target | `tag` |
| enforcement | `active` |
| conditions | `ref_name.include: ["refs/tags/v*"]`, `exclude: []` |
| rules | `deletion`, `non_fast_forward`, `update` |
| bypass actors | none (`[]`) |

A `v*` tag cannot be deleted, moved or force-updated once pushed, by anyone. Creating a new `v*`
tag is not restricted, but the release workflow refuses one that is not signed (below).

## The tags

| tag | object | signed | `git tag -v` with `.github/allowed_signers` | GitHub |
|---|---|---|---|---|
| `v0.1.0`, `v0.1.1`, `v0.2.0`, `v0.2.1` | commit (lightweight) | no | — | — |
| `v0.2.2` | tag `c6f99cad…` → commit `bad020bd…` | SSH, ED25519 | `Good "git" signature`, key `SHA256:sOtLszhygrPR/mfxW6nRe97GIXiHpTvCEi3n6ogH/LI` | `verified: true`, `valid` |
| `v0.3.0` | tag `fb925853…` → commit `7314099…` | SSH, ED25519 | the same | `verified: true`, `valid` |

Git 2.49.0 and OpenSSH 9.9p2. The key in `.github/allowed_signers` is the one key
`https://api.github.com/users/sayam/ssh_signing_keys` lists. The four tags before v0.2.2 stay as
they are: the ruleset keeps them from being moved, and nothing can sign them now without replacing them.

## The release refuses an unsigned tag

The `release-check` job of `.github/workflows/release.yml` now runs, before anything is built,
the step "the tag is annotated and signed with a key the account lists". Its commands were run
here on three tags:

| tag | result |
|---|---|
| `v0.3.0` | `Good "git" signature`, exit 0 |
| `v0.2.1` (lightweight) | "v0.2.1 is a lightweight tag: tag with git tag -s", exit 1 |
| a local tag signed with a new key not in the file (never pushed, deleted after) | `git tag -v` exit 1 |

`tests/test_release_is_bound_to_its_tag.py` holds the step in the workflow and a key of the right
form in the file.

## What this does not show

- The step has not run in a workflow yet: its first run is the release of v0.3.1. The pinned
  `actions/checkout` fetches an explicit `refs/tags/<tag>` as `+refs/tags/<tag>:refs/tags/<tag>`,
  which keeps the annotated tag object. That was read in its source, not seen in a run.
- A key both put in `.github/allowed_signers` and added to the account signs as well as this one.
  Both need the maintainer's account.
