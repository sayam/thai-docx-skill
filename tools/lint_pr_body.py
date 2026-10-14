# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A pull request's description credits nobody who did not sign (ADR 0013).

    PR_BODY="$(gh pr view 12 --json body --jq .body)" python3 tools/lint_pr_body.py
    python3 tools/lint_pr_body.py --file description.md

`tools/lint_commits.py` refuses `Co-authored-by:` and `Claude-Session:` in a commit: the person
who signed is the author, and a tool that helped write a change is not (ADR 0013). A pull
request's description is published under the same name, so it is held to the same rule.

What is refused is read by its shape in `tools/lint_credit_lines.py`, the checker the `commits` job
runs on every commit message: a trailer whose key is a credit, a line that opens with a credit verb
and `with` or `by` before a name, a link alone on its line to a session. The first version of this
file knew nine tools by name, and a footer naming a tenth passed it (planted and measured,
2026-10-14).

A description may still say what the rule refuses: a mention in the middle of a sentence, or
quoted in backticks, opens no line.

The description arrives in the environment, never on the command line and never pasted into a
script: it is text a stranger writes.

Role: decider — it answers pass or fail and returns an exit code that can block a pull request.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from lint_credit_lines import check_text  # noqa: E402  one shape, held in one place

__all__ = ["check_body", "main"]

def check_body(body: str | None) -> list[tuple[int, str]]:
    """Every refused line, as (line number, why). An empty description passes: it credits nobody."""
    return check_text(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--file", type=pathlib.Path, help="read the description from a file instead of $PR_BODY")
    args = parser.parse_args(argv)
    if args.file is not None:
        body = args.file.read_text(encoding="utf-8")
    elif "PR_BODY" in os.environ:
        body = os.environ["PR_BODY"]
    else:
        print("lint_pr_body: no description given — set PR_BODY or pass --file", file=sys.stderr)
        return 2
    problems = check_body(body)
    for number, why in problems:
        print(f"description line {number} {why}")
    if problems:
        print("\nRemove the line and save the description; the check runs again when it is edited (ADR 0013).")
        return 1
    print("the description credits nobody who did not sign")
    return 0


if __name__ == "__main__":
    sys.exit(main())
