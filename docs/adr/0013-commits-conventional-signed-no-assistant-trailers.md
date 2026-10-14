# 0013 — Commits are Conventional, signed off, and carry no assistant trailers

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The bundle's commit linter refuses `Co-authored-by:` and `Claude-Session:`
trailers and requires `Signed-off-by:` [S21]. The coding assistant working on
this repository appends exactly those trailers by default. The maintainer chose
the linter's rule.

## Decision

Every commit:

- is a Conventional Commit with a subject of at most 72 characters;
- carries `Signed-off-by:` from the maintainer (DCO 1.1 [S23]), written by
  `git commit -s`;
- carries no `Co-authored-by:`, `Claude-Session:` or other assistant trailer —
  including commits written with an assistant's help.

`tools/lint_commits.py` enforces it as the gate `conventional-commits`, entered
in the gate registry and CI together with the other gates.

Left out on purpose: crediting assistants in the history. A tool that helped
write a change is not an author under the DCO.

> **Later (2026-10-03):** the address in a commit's author field is the
> address of one of its sign-offs, compared without regard to case; the
> committer and merge commits are not held to it.
> `tools/lint_commit_authors.py` enforces it in the `commits` job as the gate
> `commit-author-signed-it`.

> **Later (2026-10-14):** a trailer and a footer are refused by their shape — a
> key that ends in `-by` or `-with` or names a session, a credit verb before a
> name, a link alone to a session — in every commit message and in the pull
> request's description, not by a list of names: a footer naming a tool the list
> did not know had passed. `tools/lint_credit_lines.py` enforces it in the
> `commits` job as the gate `credit-lines-read-by-shape`.

## Why

A sign-off certifies the right to submit the change, and only the person who
has that right can give it [S23]. A convention that lives only in an
instruction file gets overwritten by the next tool's default, so a checker is
what refuses [S21].

## Expires when

The maintainer decides to credit tools in the history — through a new record,
with the linter's rule changed in the same change.
