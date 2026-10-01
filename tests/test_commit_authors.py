# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A commit is written under an address that signed it off (ADR 0013).

Gates `commit-author-signed-it` and `commit-author-checker-proven-two-way`. The commit linter reads
the message; this reads the author field beside it. Each case is a commit made in a repository of
its own, read by the command as CI runs it.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "lint_commit_authors.py"
WORKFLOW = ROOT / ".github" / "workflows" / "gates.yml"
sys.path.insert(0, str(ROOT / "tools"))
import lint_commit_authors  # noqa: E402
import lint_commits  # noqa: E402

SIGNER = ("A Signer", "signer@example.org")
OTHER = ("Another Hand", "other@example.net")
SIGNED = f"Signed-off-by: {SIGNER[0]} <{SIGNER[1]}>"


def _git(repo: pathlib.Path, *args: str, author=SIGNER, committer=SIGNER) -> str:
    """git in `repo` under the identities given, reading no configuration but the repository's own."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME=author[0], GIT_AUTHOR_EMAIL=author[1],
               GIT_COMMITTER_NAME=committer[0], GIT_COMMITTER_EMAIL=committer[1])
    done = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def _commit(repo: pathlib.Path, subject: str, body: str = SIGNED, **who) -> str:
    _git(repo, "commit", "--allow-empty", "-m", subject, "-m", body, **who)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _commit(tmp_path, "docs: the first")
    _git(tmp_path, "tag", "base")
    return tmp_path


def _run(repo: pathlib.Path, rev_range: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), "--range", rev_range], cwd=repo, capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize("address, message", [
    (SIGNER[1], "fix: a thing\n\n" + SIGNED),
    ("Signer@Example.ORG", "fix: a thing\n\n" + SIGNED),                                   # an address is not case
    (SIGNER[1], f"fix: a thing\n\nSigned-off-by: Known By Another Name <{SIGNER[1]}>\n"),  # the address signs, not the name
    (OTHER[1], f"fix: a thing\n\nSigned-off-by: {OTHER[0]} <{OTHER[1]}>\n{SIGNED}\n"),      # a patch applied by a second signer
    (SIGNER[1], "fix: a thing\r\n\r\n" + SIGNED + "\r\n"),
])
def test_an_author_who_signed_passes(address, message):
    assert lint_commit_authors.check_author(address, message) == []


@pytest.mark.parametrize("address, message, says", [
    (OTHER[1], "fix: a thing\n\n" + SIGNED, f"is written under <{OTHER[1]}> and signed off by <{SIGNER[1]}>"),
    (OTHER[1], "fix: a thing\n", f"is written under <{OTHER[1]}> and nobody signed it off"),
    ("", "fix: a thing\n\n" + SIGNED, "names no author address"),
    # the address stands in the message, but not as the address of a sign-off
    (OTHER[1], f"fix: a thing\n\nReported by {OTHER[1]}.\n\n{SIGNED}", "signed off by"),
    (OTHER[1], f"fix: a thing\n\nCo-authored-by: {OTHER[0]} <{OTHER[1]}>\n{SIGNED}", "signed off by"),
    (OTHER[1], f"fix: a thing\n\nSigned-off-by: {OTHER[1]} <{SIGNER[1]}>", "signed off by"),
    (OTHER[1], f"fix: a thing\n\n    Signed-off-by: {OTHER[0]} <{OTHER[1]}>\n\n{SIGNED}", "signed off by"),  # quoted, not a trailer
    (SIGNER[1][:-1], "fix: a thing\n\n" + SIGNED, "signed off by"),                                           # nearly the address
])
def test_an_author_who_did_not_sign_is_refused(address, message, says):
    problems = lint_commit_authors.check_author(address, message)
    assert len(problems) == 1 and says in problems[0] and "ADR 0013" in problems[0], problems


def test_a_branch_of_the_signers_own_commits_passes(repo):
    _commit(repo, "fix: one")
    _commit(repo, "docs: two", body="A body\nof two lines.\n\n" + SIGNED)
    done = _run(repo, "base..HEAD")
    assert done.returncode == 0 and done.stderr == "", done
    assert done.stdout == "every commit is written under an address that signed it\n"


def test_a_commit_written_under_an_address_that_did_not_sign_is_named(repo, monkeypatch):
    """The fault this holds: the message check alone passes a commit that another address wrote and
    the signer only signed, so the history credits an address that certified nothing."""
    _commit(repo, "fix: one")
    planted = _commit(repo, "fix: written by another hand", author=OTHER)
    _commit(repo, "fix: three")
    monkeypatch.chdir(repo)
    assert lint_commits.main(["--range", "base..HEAD"]) == 0, "the message carries a sign-off and no refused trailer"
    done = _run(repo, "base..HEAD")
    assert done.returncode == 1 and done.stderr == "", done
    lines = done.stdout.splitlines()
    assert len(lines) == 1 and lines[0].startswith(f"FAIL {planted[:9]}: is written under <{OTHER[1]}> and signed off by <{SIGNER[1]}>"), lines
    # what a rebase with --signoff leaves: the committer is the signer, the author is still the other
    assert _git(repo, "log", "-1", "--format=%ae %ce", planted) == f"{OTHER[1]} {SIGNER[1]}"


def test_the_commit_passes_once_its_author_is_the_signer(repo):
    _commit(repo, "fix: written by another hand", author=OTHER)
    assert _run(repo, "base..HEAD").returncode == 1
    _git(repo, "commit", "--amend", "--allow-empty", "--no-edit", "--reset-author")
    assert _run(repo, "base..HEAD").returncode == 0


def test_the_committer_is_not_held_to_it(repo):
    """A maintainer who rebases, and the platform's merge button, commit what another wrote and signed."""
    _commit(repo, "fix: one", committer=OTHER)
    assert _run(repo, "base..HEAD").returncode == 0


def test_a_merge_commit_is_left_out_as_the_commit_linter_leaves_it(repo):
    _git(repo, "switch", "-q", "-c", "side")
    _commit(repo, "fix: on the side")
    _git(repo, "switch", "-q", "main")
    _commit(repo, "fix: on main")
    _git(repo, "merge", "-q", "--no-ff", "-m", "Merge branch 'side'", "side", author=OTHER, committer=OTHER)
    assert _git(repo, "log", "-1", "--format=%ae %p").startswith(OTHER[1] + " ") and " " in _git(repo, "log", "-1", "--format=%p")
    assert _run(repo, "base..HEAD").returncode == 0


def test_only_the_range_is_read(repo):
    _commit(repo, "fix: written by another hand", author=OTHER)
    _git(repo, "tag", "after")
    _commit(repo, "fix: the signer's own")
    assert _run(repo, "base..HEAD").returncode == 1 and _run(repo, "after..HEAD").returncode == 0


def test_a_message_of_many_lines_is_one_commit():
    out = (f"{'a' * 40}\x00{SIGNER[1]}\x00fix: one\n\nline\n\n{SIGNED}\n\x1e\n"
           f"{'b' * 40}\x00{OTHER[1]}\x00fix: two\n\n{SIGNED}\n\x1e\n")
    commits = lint_commit_authors.parse_log(out)
    assert [(sha, address) for sha, address, _ in commits] == [("a" * 9, SIGNER[1]), ("b" * 9, OTHER[1])]
    assert commits[0][2].count("\n") >= 4 and lint_commit_authors.signers(commits[1][2]) == [SIGNER[1]]
    # the format handed to git and the separators it is split on are one choice
    assert lint_commit_authors.LOG_FORMAT == "%H%x00%ae%x00%B%x1e"
    assert (lint_commit_authors.FIELD_SEP, lint_commit_authors.RECORD_SEP) == ("\x00", "\x1e")


def test_a_history_that_cannot_be_read_is_no_verdict(repo, monkeypatch, capsys):
    done = _run(repo, "no-such-ref..HEAD")
    assert done.returncode == 2 and done.stdout == "" and done.stderr.startswith("cannot read the history: `git log no-such-ref..HEAD` failed:")
    nothing = subprocess.run([sys.executable, str(TOOL)], cwd=repo, capture_output=True, text=True, timeout=60)
    assert nothing.returncode == 2 and "--range" in nothing.stderr, "silence is not a pass"

    def never_answers(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(lint_commit_authors.subprocess, "run", never_answers)
    assert lint_commit_authors.main(["--range", "base..HEAD"]) == 2
    assert f"did not answer within {lint_commit_authors.LOCAL_TIMEOUT_SECONDS} seconds" in capsys.readouterr().err


def test_an_address_that_is_not_utf8_is_refused_in_words(repo):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="x", GIT_COMMITTER_NAME=SIGNER[0],
               GIT_COMMITTER_EMAIL=SIGNER[1])
    made = subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-q", "-m", "fix: one", "-m", SIGNED],
                          cwd=repo, env={k: os.fsencode(v) for k, v in env.items()} | {b"GIT_AUTHOR_EMAIL": b"caf\xe9@example.net"},
                          capture_output=True, timeout=60)
    assert made.returncode == 0, made.stderr
    done = _run(repo, "base..HEAD")
    assert done.returncode == 1 and "FAIL " in done.stdout and "@example.net> and signed off by" in done.stdout, done


def test_the_workflow_reads_the_authors_of_the_commits_it_lints():
    text = WORKFLOW.read_text(encoding="utf-8")
    commits = text.split("\n  commits:\n", 1)[1].split("\n  tests:\n", 1)[0]
    runs = [line.strip() for line in commits.split("\n") if line.strip().startswith("python3 tools/")]
    assert runs == ['python3 tools/lint_commits.py --range "$range"', 'python3 tools/lint_commit_authors.py --range "$range"']
    assert "fetch-depth: 0" in commits and "continue-on-error" not in commits
