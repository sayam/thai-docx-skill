# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A commit is written under an address that signed it off (ADR 0013).

    python3 tools/lint_commit_authors.py --range main..HEAD

`tools/lint_commits.py` reads a commit's message: it must carry a `Signed-off-by:` line and no
trailer that credits somebody who did not sign. The message is not the only place a commit names
who wrote it. The author field is what `git log` and the platform show as the author, and what the
platform counts as a contributor; a commit written under one address and signed off by another
passes the message check and still credits an address that certified nothing.

So the address in a commit's author field must be the address of one of its sign-offs, compared
without regard to case.

The committer is not held to this. Whoever rebases a branch or applies a patch commits what another
person wrote and signed, and the platform's merge button commits under an address of its own.
Merge commits are left out, as the commit linter leaves them out: the platform writes them.

Role: decider — it answers pass or fail and returns an exit code that can block a pull request.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

__all__ = ["check_author", "commits_in_range", "main", "parse_log", "signers"]

# a `git` that never answers must not eat the job's whole budget (as in lint_commits.py)
LOCAL_TIMEOUT_SECONDS = 60

# the address of each sign-off, in the shape `git commit -s` writes and lint_commits.py requires
SIGNER = re.compile(r"^Signed-off-by: [^<>]*<([^<>\s]+)>\s*$", re.MULTILINE)

# A message holds newlines, so a record ends at a byte no message holds; the same choice, for the
# same reason, as lint_commits.py makes.
RECORD_SEP = "\x1e"
FIELD_SEP = "\x00"
LOG_FORMAT = "%H%x00%ae%x00%B%x1e"


def signers(message: str) -> list[str]:
    """The address of every sign-off in a message, in the order written."""
    return SIGNER.findall(message)


def check_author(address: str, message: str) -> list[str]:
    """What is wrong with one commit's author, as a list — empty means pass."""
    signed = signers(message)
    if address and address.lower() in {s.lower() for s in signed}:
        return []
    said = f"is written under <{address}>" if address else "names no author address"
    by = "and signed off by " + ", ".join(f"<{s}>" for s in signed) if signed else "and nobody signed it off"
    return [
        f"{said} {by} — the author of a commit is a person who signed it (ADR 0013); "
        "as its author, `git commit --amend --reset-author -s` writes both"
    ]


def parse_log(out: str) -> list[tuple[str, str, str]]:
    """Turn `git log --format=LOG_FORMAT` output into (short sha, author address, message)."""
    return [
        (sha[:9], address, message)
        for chunk in out.split(RECORD_SEP)
        if chunk.strip()
        for sha, address, message in [chunk.strip("\n").split(FIELD_SEP, 2)]
    ]


def commits_in_range(rev_range: str) -> list[tuple[str, str, str]]:
    """The commits in this range, merge commits excluded. A range git cannot read, or does not
    answer for in time, is a RuntimeError that says so: no verdict on anybody's commits."""
    try:
        out = subprocess.run(  # the range comes from CI or the developer, never from a commit
            ["git", "log", "--no-merges", f"--format={LOG_FORMAT}", rev_range],
            capture_output=True,
            check=True,
            timeout=LOCAL_TIMEOUT_SECONDS,
        ).stdout
    except subprocess.TimeoutExpired as expired:
        raise RuntimeError(f"`git log {rev_range}` did not answer within {LOCAL_TIMEOUT_SECONDS} seconds") from expired
    except subprocess.CalledProcessError as failed:
        raise RuntimeError(f"`git log {rev_range}` failed: {failed.stderr.decode('utf-8', 'replace').strip()}") from failed
    # an address or a message is bytes; one that is not UTF-8 is carried through and compared as it is
    return parse_log(out.decode("utf-8", "surrogateescape"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--range", dest="rev_range", required=True, help="a commit range, as `git log` takes one")
    args = parser.parse_args(argv)
    try:
        commits = commits_in_range(args.rev_range)
    except RuntimeError as unreadable:
        print(f"cannot read the history: {unreadable}", file=sys.stderr)
        return 2
    failures = [(sha, problem) for sha, address, message in commits for problem in check_author(address, message)]
    for sha, problem in failures:
        print(f"FAIL {sha}: {problem}".encode("utf-8", "backslashreplace").decode("utf-8"))
    if not failures:
        print("every commit is written under an address that signed it")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
