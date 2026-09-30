# 0042 — The maintainer's working notes travel encrypted, and do nothing in anyone else's clone

- Status: accepted
- Decided: 2026-09-30

## Where it came from

The maintainer keeps plans, review notes, run scripts and lists for the next release in `.local/`,
which git ignores: they never reach this public repository. Work that goes on in a cloud session
while the workstation is off cannot see them, and what that session writes does not come back.
The maintainer asked for `.local/` to travel through a private repository holding ciphertext only,
with the rules and memory the work is done under, and for one side at a time to work on it
(the plan of 0.3.3, §6, 2026-09-30).

## Decision

`tools/dotlocal.py` mirrors part of `.local/`, `~/.claude/CLAUDE.md` and this project's memory into
`.local.asc/`, a clone of the private repository `dotlocal` on a branch named after this repository,
every file a gpg symmetric ciphertext (AES-256, `--rfc4880`, so gpg 2.2 reads it; the passphrase on
a pipe, never on a command line). The list of what travels, with the sha256 of each plaintext, is
encrypted too. A change is found three ways — here now, here at the last sync, the remote — so a
file both sides changed is kept beside the other (`.dotlocal-remote`) and a push is refused until
it is settled. `.local.asc/` is reset to the remote, never merged.

- **It lives in this repository**, because a cloud session runs only the hooks of the repository
  it clones: `.claude/settings.json` pulls at `SessionStart`, checks the lock at `PreToolUse`, and
  releases at `SessionEnd`; `git push` pushes, through a `pre-push` hook it installs only where
  none is.

  > **Later (2026-10-01):** there is no `SessionEnd` hook. Claude Code cancelled it when a session
  > ended, before its push and release could finish, and said it failed; the lock is given up only
  > by `tools/dotlocal.py release`.
- **Without a passphrase it does nothing and exits 0.** A clone or a fork of this repository, and
  anyone who contributes to it, is not touched; its hooks pass every tool call.
- **What travels is an allow-list**: text files of at most 1 MB under `.local/`, but for `secrets/`,
  the folders a tool makes again and what `.local/.dotlocalignore` names. `.local/` holds gigabytes
  of copies and outputs that a cloud session does not need. A file that stops travelling is not
  deleted on the other side.
- **One side works at a time**: a `LOCK` file in the same branch, written by a push, so two sides
  cannot both win; the side that does not hold it is refused edits and commands until the other
  releases it, or the maintainer takes it with `take --force` typed in a terminal.
- `.claude/settings.json` also sets `"attribution": false`, so no session writes an assistant's
  line into a commit or a pull request here (ADR 0013); the linters still decide.

Left out on purpose: syncing binary files and whole run folders, a key per file or public-key
encryption (one passphrase per repository is what the maintainer chose), and any coverage of the
tool by `.coveragerc`, which measures the skill; `tests/test_dotlocal.py` holds it instead.
`.claude/` is `export-ignore`d with the rest of the development files (ADR 0018).

## Why

Plaintext notes in a public repository would publish them; notes left on one machine stop the
work when it is off. Ciphertext in a private repository keeps the first and ends the second, and a
tool that does nothing without its passphrase costs nothing to anyone else who clones this one.

## Expires when

The work no longer runs in cloud sessions, or those sessions can reach the workstation's files
directly; or the maintainer moves the notes somewhere this repository does not reach.
