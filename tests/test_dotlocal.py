# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""tools/dotlocal.py against a bare repository in a temporary directory (ADR 0042).

Two machines are two checkouts, each with its own HOME, `.local/` and `.local.asc/`; the private
repository is a bare one beside them. Every acceptance criterion the maintainer set is a test here:
nothing is done without a passphrase, bytes and Thai names come back as they went, edits and
deletions travel both ways, a conflict is kept beside the file and blocks the push, a wrong
passphrase touches nothing, `git push` runs the sync and a failed sync does not stop it, another
pre-push hook is left alone, and the ciphertext is what gpg 2.2 reads. Then the lock, and what
travels.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "dotlocal.py"
SECRET = "correct horse battery staple"

pytestmark = pytest.mark.skipif(shutil.which("gpg") is None and not os.environ.get("CI"), reason="gpg is not installed")


def run(args: list[str], cwd: pathlib.Path, env: dict, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, input=stdin, timeout=120)


def git(cwd: pathlib.Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.invalid",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.invalid"})
    assert done.returncode == 0, done.stderr
    return done.stdout


class Machine:
    """A checkout of the main repository with a HOME of its own."""

    def __init__(self, tmp: pathlib.Path, name: str, remote: pathlib.Path, origin: pathlib.Path, cloud: bool = False):
        self.root = tmp / name / "thai-docx-skill"
        self.home = tmp / name / "home"
        self.home.mkdir(parents=True)
        (self.home / "gnupg").mkdir(mode=0o700)
        subprocess.run(["git", "clone", "--quiet", str(origin), str(self.root)], check=True, timeout=60)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "CLAUDE_", "DOTLOCAL_"))}
        self.env.update({"HOME": str(self.home), "GNUPGHOME": str(self.home / "gnupg"), "DOTLOCAL_REMOTE": str(remote),
                         "DOTLOCAL_BRANCH": "thai-docx-skill", "DOTLOCAL_PASSPHRASE": SECRET,
                         "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.invalid",
                         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.invalid"})
        if cloud:
            self.env["CLAUDE_CODE_REMOTE"] = "true"
        self.local = self.root / ".local"
        self.local.mkdir()

    def dl(self, *args: str, env: dict | None = None, stdin: str = "") -> subprocess.CompletedProcess:
        return run([sys.executable, str(TOOL), *args], self.root, env or self.env, stdin)

    def write(self, rel: str, data: bytes | str) -> pathlib.Path:
        path = self.local / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def memory(self) -> pathlib.Path:
        import re
        return self.home / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(self.root)) / "memory"

    def manifest(self) -> dict:
        f = self.root / ".local.asc" / ".dotlocal-manifest.asc"
        done = subprocess.run(["gpg", "--batch", "--quiet", "--pinentry-mode", "loopback", "--passphrase", SECRET, "--decrypt", str(f)],
                              capture_output=True, env=self.env, timeout=60)
        assert done.returncode == 0, done.stderr
        return json.loads(done.stdout)


@pytest.fixture()
def world(tmp_path):
    remote = tmp_path / "dotlocal.git"
    subprocess.run(["git", "init", "--quiet", "--bare", "-b", "main", str(remote)], check=True, timeout=60)
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--quiet", "--bare", "-b", "main", str(origin)], check=True, timeout=60)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(seed)], check=True, timeout=60)
    (seed / "README.md").write_text("main repository\n", encoding="utf-8")
    (seed / ".gitignore").write_text(".local/\n.local.asc/\n", encoding="utf-8")
    (seed / "tools").mkdir()
    shutil.copy(TOOL, seed / "tools" / "dotlocal.py")  # the pre-push hook runs the checkout's own copy
    git(seed, "add", "-A")
    git(seed, "commit", "--quiet", "-m", "seed")
    git(seed, "push", "--quiet", str(origin), "main")
    made: list[Machine] = []

    def machine(name: str, cloud: bool = False) -> Machine:
        m = Machine(tmp_path, name, remote, origin, cloud)
        made.append(m)
        return m

    machine.remote = remote
    yield machine
    for m in made:
        subprocess.run(["gpgconf", "--kill", "all"], env=m.env, capture_output=True, timeout=30)


def commits(remote: pathlib.Path) -> int:
    done = subprocess.run(["git", "rev-list", "--count", "thai-docx-skill"], cwd=remote, capture_output=True, text=True, timeout=30)
    return int(done.stdout.strip() or 0) if done.returncode == 0 else 0


def tree(path: pathlib.Path) -> dict[str, str]:
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob("*")) if p.is_file()}


def test_without_a_passphrase_nothing_is_done(world):
    a = world("a")
    a.write("README.md", "notes\n")
    bare = {k: v for k, v in a.env.items() if k != "DOTLOCAL_PASSPHRASE"}
    for command in ("pull", "push", "session-start", "status", "install", "release"):
        done = a.dl(command, env=bare)
        assert done.returncode == 0 and done.stdout == "", (command, done)
    done = a.dl("lock-check", env=bare, stdin=json.dumps({"tool_name": "Edit", "tool_input": {}}))
    assert done.returncode == 0 and done.stdout == ""
    assert not (a.root / ".local.asc").exists() and commits(world.remote) == 0
    assert not (a.root / ".git" / "hooks" / "pre-push").exists()


def test_a_first_push_commits_and_a_push_with_nothing_new_does_not(world):
    a = world("a")
    a.write("README.md", "notes\n")
    assert a.dl("push").returncode == 0 and commits(world.remote) == 1
    done = a.dl("push")
    assert done.returncode == 0 and "nothing changed" in done.stdout and commits(world.remote) == 1


def test_bytes_and_thai_names_come_back_as_they_went(world):
    a, b = world("a"), world("b")
    raw = bytes(range(256)) * 4
    a.write("work/ทดลอง/ข้อมูล ดิบ.txt", raw)
    a.write("work/ทดลอง/บันทึก.md", "สระอำ ทำ น้ำ — ฐานข้อมูล ๑๒๓\n")
    assert a.dl("push").returncode == 0
    assert b.dl("pull").returncode == 0
    assert (b.local / "work/ทดลอง/ข้อมูล ดิบ.txt").read_bytes() == raw
    assert (b.local / "work/ทดลอง/บันทึก.md").read_bytes() == (a.local / "work/ทดลอง/บันทึก.md").read_bytes()


def test_edits_and_deletions_travel_both_ways(world):
    a, b = world("a"), world("b")
    a.write("work/p/PLAN.md", "one\n")
    a.write("work/p/old.md", "old\n")
    assert a.dl("push").returncode == 0 and b.dl("pull").returncode == 0
    b.write("work/p/PLAN.md", "two\n")
    (b.local / "work/p/old.md").unlink()
    assert b.dl("push").returncode == 0 and a.dl("pull").returncode == 0
    assert (a.local / "work/p/PLAN.md").read_text() == "two\n" and not (a.local / "work/p/old.md").exists()
    a.write("work/p/PLAN.md", "three\n")
    a.write("work/p/new.md", "new\n")
    assert a.dl("push").returncode == 0 and b.dl("pull").returncode == 0
    assert (b.local / "work/p/PLAN.md").read_text() == "three\n" and (b.local / "work/p/new.md").read_text() == "new\n"


def test_a_conflict_is_kept_beside_the_file_and_blocks_the_push_until_settled(world):
    a, b = world("a"), world("b")
    a.write("work/p/PLAN.md", "base\n")
    assert a.dl("push").returncode == 0 and b.dl("pull").returncode == 0
    a.write("work/p/PLAN.md", "from a\n")
    assert a.dl("push").returncode == 0
    b.write("work/p/PLAN.md", "from b\n")
    done = b.dl("pull")
    assert done.returncode == 0 and "both sides changed" in done.stdout
    assert (b.local / "work/p/PLAN.md").read_text() == "from b\n"
    assert (b.local / "work/p/PLAN.md.dotlocal-remote").read_text() == "from a\n"
    done = b.dl("push")
    assert done.returncode == 1 and "settle these first" in done.stderr
    (b.local / "work/p/PLAN.md.dotlocal-remote").unlink()
    assert b.dl("push").returncode == 0 and a.dl("pull").returncode == 0
    assert (a.local / "work/p/PLAN.md").read_text() == "from b\n"


def test_a_wrong_passphrase_touches_nothing(world):
    a, b = world("a"), world("b")
    a.write("work/p/PLAN.md", "one\n")
    assert a.dl("push").returncode == 0
    b.write("work/p/PLAN.md", "mine\n")
    b.write("work/p/only-here.md", "b\n")
    before = tree(b.local)
    wrong = {**b.env, "DOTLOCAL_PASSPHRASE": "not it"}
    for command in ("pull", "push"):
        done = b.dl(command, env=wrong)
        assert done.returncode != 0 and "passphrase" in done.stderr, done
    assert tree(b.local) == before


def test_git_push_runs_the_sync_and_a_failed_sync_does_not_stop_it(world):
    a = world("a")
    assert a.dl("install").returncode == 0
    a.write("work/p/PLAN.md", "one\n")
    (a.root / "file.txt").write_text("x\n", encoding="utf-8")
    git(a.root, "add", "file.txt")
    git(a.root, "commit", "--quiet", "-m", "x")
    done = subprocess.run(["git", "push", "--quiet", "origin", "main"], cwd=a.root, env=a.env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and commits(world.remote) == 1, done.stderr
    a.write("work/p/PLAN.md", "two\n")
    git(a.root, "commit", "--quiet", "--allow-empty", "-m", "y")
    wrong = {**a.env, "DOTLOCAL_PASSPHRASE": "not it"}
    done = subprocess.run(["git", "push", "--quiet", "origin", "main"], cwd=a.root, env=wrong, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and "the sync failed; the push goes on" in done.stderr and commits(world.remote) == 1


def test_another_pre_push_hook_is_left_alone(world):
    a = world("a")
    hook = a.root / ".git" / "hooks" / "pre-push"
    hook.write_text("#!/bin/sh\necho theirs\n", encoding="utf-8")
    done = a.dl("install")
    assert done.returncode == 0 and "left alone" in done.stdout
    assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho theirs\n"


def test_the_ciphertext_is_what_gpg_2_2_reads(world):
    a = world("a")
    a.write("README.md", "notes\n")
    assert a.dl("push").returncode == 0
    packets = subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", SECRET, "--list-packets",
                              str(a.root / ".local.asc" / "README.md.asc")], capture_output=True, text=True, env=a.env, timeout=60)
    listing = packets.stdout + packets.stderr
    assert "mdc_method: 2" in listing and "cipher 9" in listing, listing
    assert "aead" not in listing.replace("aead 0", "").lower(), listing
    assert (a.root / ".local.asc" / "README.md.asc").read_text().startswith("-----BEGIN PGP MESSAGE-----")


def test_the_passphrase_never_reaches_a_command_line(world, tmp_path):
    a = world("a")
    shim = tmp_path / "shim"
    shim.mkdir()
    log = tmp_path / "argv.log"
    real = shutil.which("gpg")
    (shim / "gpg").write_text(f"#!/bin/sh\necho \"$@\" >> '{log}'\nexec '{real}' \"$@\"\n", encoding="utf-8")
    (shim / "gpg").chmod(0o755)
    a.write("README.md", "notes\n")
    env = {**a.env, "PATH": f"{shim}{os.pathsep}{a.env['PATH']}"}
    assert a.dl("push", env=env).returncode == 0
    argv = log.read_text(encoding="utf-8")
    assert "--passphrase-fd" in argv and SECRET not in argv and "--rfc4880" in argv


def test_what_travels_is_the_allow_list(world):
    a, b = world("a"), world("b", cloud=True)
    a.write(".dotlocalignore", "work/closed*\n")
    a.write("README.md", "notes\n")
    a.write("work/open/PLAN.md", "plan\n")
    a.write("work/closed-review/PLAN.md", "done\n")
    a.write("secrets/anthropic-api-key", "sk-not-real\n")
    a.write("secrets/token.txt", "not-real\n")  # a text file: only the rule for secrets/ keeps it back
    a.write("work/open/venv/lib/x.py", "x\n")
    a.write("work/open/pytest-0/y.md", "y\n")
    a.write("work/open/shot.png", b"\x89PNG")
    a.write("work/open/big.md", "x" * 2000)
    (a.local / "work/open/link.md").symlink_to(a.local / "README.md")
    rules = a.home / ".claude" / "CLAUDE.md"
    rules.parent.mkdir(parents=True)
    rules.write_text("# the rules\n", encoding="utf-8")
    a.memory().mkdir(parents=True)
    (a.memory() / "MEMORY.md").write_text("- [one](one.md)\n", encoding="utf-8")
    env = {**a.env, "DOTLOCAL_MAX_BYTES": "1000"}
    done = a.dl("push", env=env)
    assert done.returncode == 0, done.stderr
    assert sorted(a.manifest()) == ["claude/CLAUDE.md", "claude/memory/MEMORY.md", "local/.dotlocalignore",
                                    "local/README.md", "local/work/open/PLAN.md"]
    assert "over 1000 bytes" in done.stdout and "symbolic link" in done.stdout
    done = b.dl("session-start")
    assert done.returncode == 0 and "# the rules" in done.stdout and "- [one](one.md)" in done.stdout, done
    assert (b.memory() / "MEMORY.md").read_text() == "- [one](one.md)\n"
    assert (b.home / ".claude" / "CLAUDE.md").read_text() == "# the rules\n"


def test_leaving_the_allow_list_deletes_nothing_on_the_other_side(world):
    a, b = world("a"), world("b")
    a.write("work/p/PLAN.md", "plan\n")
    assert a.dl("push").returncode == 0 and b.dl("pull").returncode == 0
    a.write(".dotlocalignore", "work/p\n")
    assert a.dl("push").returncode == 0 and b.dl("pull").returncode == 0
    assert (b.local / "work/p/PLAN.md").read_text() == "plan\n"
    assert "local/work/p/PLAN.md" in a.manifest()


def test_a_file_held_back_here_is_left_as_it_is(world):
    """A file too big to travel on one side is neither overwritten nor shadowed by the other's copy."""
    a, b = world("a"), world("b")
    a.write("work/p/notes.md", "small\n")
    assert a.dl("push").returncode == 0 and b.dl("pull").returncode == 0
    b.write("work/p/notes.md", "x" * 2000)
    a.write("work/p/notes.md", "changed on a\n")
    assert a.dl("push").returncode == 0
    done = b.dl("pull", env={**b.env, "DOTLOCAL_MAX_BYTES": "1000"})
    assert done.returncode == 0 and "over 1000 bytes" in done.stdout
    assert (b.local / "work/p/notes.md").read_text() == "x" * 2000
    assert not (b.local / "work/p/notes.md.dotlocal-remote").exists()


def test_one_side_works_at_a_time(world):
    a, b = world("a"), world("b", cloud=True)
    a.write("README.md", "notes\n")
    edit = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "x"}})
    assert a.dl("session-start").returncode == 0
    assert a.dl("lock-check", stdin=edit).stdout == ""
    done = b.dl("session-start")
    assert done.returncode == 0 and "the local side holds the lock" in done.stdout
    refused = json.loads(b.dl("lock-check", stdin=edit).stdout)["hookSpecificOutput"]
    assert refused["permissionDecision"] == "deny" and "local side" in refused["permissionDecisionReason"]
    ask = json.dumps({"tool_name": "Bash", "tool_input": {"command": "python3 tools/dotlocal.py status"}})
    assert b.dl("lock-check", stdin=ask).stdout == ""
    done = b.dl("take", "--force")
    assert done.returncode == 1 and "typed in a terminal" in done.stderr
    (a.root / "file.txt").write_text("x\n", encoding="utf-8")
    git(a.root, "add", "file.txt")
    git(a.root, "commit", "--quiet", "-m", "x")
    done = a.dl("release")
    assert done.returncode == 1 and "not pushed" in done.stderr
    git(a.root, "push", "--quiet", "origin", "main")
    assert a.dl("release").returncode == 0
    assert b.dl("session-start").returncode == 0
    assert b.dl("lock-check", stdin=edit).stdout == ""
    refused = json.loads(a.dl("lock-check", stdin=edit).stdout)["hookSpecificOutput"]
    assert refused["permissionDecision"] == "deny" and "cloud side" in refused["permissionDecisionReason"]


def test_two_sides_claiming_at_once_one_loses(world, monkeypatch):
    a, b = world("a"), world("b", cloud=True)
    a.write("README.md", "notes\n")
    assert a.dl("pull").returncode == 0 and b.dl("pull").returncode == 0
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import dotlocal
    finally:
        sys.path.remove(str(ROOT / "tools"))
    for key in list(os.environ):
        if key.startswith(("CLAUDE_", "DOTLOCAL_")):
            monkeypatch.delenv(key)
    for key, value in b.env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.chdir(b.root)
    place = dotlocal.Place()
    # b wrote its claim while a's landed first: the push is not a fast-forward, and b does not hold it
    assert a.dl("session-start").returncode == 0
    (place.asc / dotlocal.LOCK).write_text(json.dumps({"side": "cloud"}), encoding="utf-8")
    assert dotlocal.commit_and_push(place, "lock: cloud") is False
    assert dotlocal.claim(place, "s", forced=False) is False
    assert dotlocal.lock_of(place)["side"] == "local"


def test_an_unreachable_repository_is_said_plainly(world, tmp_path):
    a = world("a", cloud=True)
    env = {**a.env, "DOTLOCAL_REMOTE": str(tmp_path / "missing.git")}
    done = a.dl("session-start", env=env)
    assert done.returncode == 0 and "attach the dotlocal repository" in done.stdout
    done = a.dl("pull", env=env)
    assert done.returncode == 1 and "cannot reach" in done.stdout
