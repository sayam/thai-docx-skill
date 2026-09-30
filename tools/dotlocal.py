#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Keep the maintainer's working notes in step between a workstation and a cloud session.

`.local/` is git-ignored and never leaves the machine in the clear. This mirrors part of it — and
the rules and memory Claude Code reads — into `.local.asc/`, a clone of the private repository
`dotlocal` on a branch named after this one, where every file is a gpg ciphertext (ADR 0042):

    python3 tools/dotlocal.py pull            # take what the other side pushed
    python3 tools/dotlocal.py push            # pull first, then send what changed here
    python3 tools/dotlocal.py status          # who holds the lock, and what differs
    python3 tools/dotlocal.py release         # push, check the branch is pushed, give the lock up
    python3 tools/dotlocal.py take --force    # take the lock from the other side (typed in a terminal)
    python3 tools/dotlocal.py install         # the git pre-push hook, if none is there

The hooks of `.claude/settings.json` call `session-start`, `lock-check` and `session-end`.
**Without a passphrase every command does nothing and exits 0**: a clone of this public repository
is not touched. The passphrase is `DOTLOCAL_PASSPHRASE`, or `~/.config/dotlocal/<branch>.passphrase`
(mode 600); `DOTLOCAL_REMOTE` and `DOTLOCAL_BRANCH` default to `origin` with the repository name
replaced by `dotlocal`, and to the repository name.

What travels (an allow-list, decided 2026-09-30): `~/.claude/CLAUDE.md`, this project's memory, and
text files of at most `DOTLOCAL_MAX_BYTES` (1 MB) in `.local/`, except `secrets/`, the folders a
tool makes again (`venv`, `repo`, `tmp`, `pytest*`, …) and what `.local/.dotlocalignore` names
(fnmatch, one pattern a line, matched against the path and every folder above it).

A change is found by the sha256 of the plaintext, three ways: L (here now), B (here at the last
sync, kept in `.local.asc/.git/`) and R (the remote's manifest, itself encrypted). Pull writes R
where L == B, leaves local changes for push, and writes `<name>.dotlocal-remote` beside a file both
sides changed; push refuses while one is there. `.local.asc/` is derived: it is reset to the remote,
never merged.

Role: a maintainer's tool. It is not part of the skill and ships in no archive (ADR 0018).
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import time

GIT_TIMEOUT = 120
GPG_TIMEOUT = 60
FETCH_TIMEOUT = 10
# seconds between the lock check's fetches: 0, so a lock taken on the other side stops this one at
# its next tool call (PLAN §6.1); a fetch that fails leaves the last lock seen in force
FETCH_EVERY = float(os.environ.get("DOTLOCAL_FETCH_EVERY", "0"))
MAX_BYTES = int(os.environ.get("DOTLOCAL_MAX_BYTES", "1000000"))
TEXT = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".toml", ".cfg", ".js", ".cjs", ".csv"}
# folders a tool writes again from what is kept, or scratch a run leaves behind
DERIVED = {"venv", ".venv", "node_modules", "tmp", "home", "repo", "__pycache__", ".pytest_cache",
           "lo", "lo-out", "try", "cases", "runs", ".ruff_cache"}
DERIVED_PREFIX = ("pytest", "scratch", "traces")
NEVER = ("secrets",)
REMOTE_SUFFIX = ".dotlocal-remote"
MANIFEST = ".dotlocal-manifest.asc"
LOCK = "LOCK"
HOOK_MARK = "# dotlocal: pushes .local/ to its encrypted private repository on every git push"
GPG_COMMON = ["--batch", "--quiet", "--pinentry-mode", "loopback", "--no-symkey-cache"]
GPG_ENCRYPT = ["--symmetric", "--cipher-algo", "AES256", "--s2k-digest-algo", "SHA512", "--rfc4880", "--armor"]


class Fault(Exception):
    """A stop with a reason for the person: exit 1, nothing half-written."""


class Unreachable(Fault):
    pass


# --- where things are --------------------------------------------------------------------------

def _git_env() -> dict:
    # a git hook runs with GIT_DIR and friends pointing at the main repository; .local.asc/ is another
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(args: list[str], cwd: pathlib.Path, check: bool = True, timeout: float = GIT_TIMEOUT) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=_git_env())
    if check and done.returncode != 0:
        raise Fault("git " + " ".join(args[:2]) + " failed: " + (done.stderr or done.stdout).strip()[-400:])
    return done


class Place:
    def __init__(self) -> None:
        start = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        top = git(["rev-parse", "--show-toplevel"], start, check=False)
        if top.returncode != 0:
            raise Fault("not inside a git repository: " + str(start))
        self.root = pathlib.Path(top.stdout.strip())
        self.local = self.root / ".local"
        self.asc = self.root / ".local.asc"
        origin = git(["remote", "get-url", "origin"], self.root, check=False).stdout.strip()
        name = re.sub(r"\.git$", "", origin.rstrip("/").split("/")[-1].split(":")[-1]) or self.root.name
        self.branch = os.environ.get("DOTLOCAL_BRANCH") or name
        self.remote = os.environ.get("DOTLOCAL_REMOTE") or (re.sub(r"[^/:]+?(\.git)?$", r"dotlocal\1", origin) if origin else "")
        home = pathlib.Path(os.environ.get("HOME") or pathlib.Path.home())
        self.home = home
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(self.root))
        self.rules = home / ".claude" / "CLAUDE.md"
        self.memory = home / ".claude" / "projects" / slug / "memory"
        self.base_file = self.asc / ".git" / "dotlocal-base.json"
        self.side = "cloud" if os.environ.get("CLAUDE_CODE_REMOTE") == "true" else "local"

    def passphrase(self) -> str | None:
        given = os.environ.get("DOTLOCAL_PASSPHRASE")
        if given:
            return given
        f = self.home / ".config" / "dotlocal" / (self.branch + ".passphrase")
        if not f.is_file():
            return None
        if f.stat().st_mode & 0o077:
            raise Fault(f"{f} is readable by others; chmod 600 it first")
        return f.read_text(encoding="utf-8").strip() or None

    # a logical key → the file on this machine, and the ciphertext in .local.asc/
    def plain(self, key: str) -> pathlib.Path:
        if key == "claude/CLAUDE.md":
            return self.rules
        if key.startswith("claude/memory/"):
            return self.memory / key[len("claude/memory/"):]
        return self.local / key[len("local/"):]

    def cipher(self, key: str) -> pathlib.Path:
        if key.startswith("claude/"):
            return self.asc / "_claude" / (key[len("claude/"):] + ".asc")
        return self.asc / (key[len("local/"):] + ".asc")


# --- what travels ------------------------------------------------------------------------------

def ignore_patterns(place: Place) -> list[str]:
    f = place.local / ".dotlocalignore"
    if not f.is_file():
        return []
    return [line.strip() for line in f.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def in_scope(rel: str, patterns: list[str]) -> bool:
    """Whether a path under .local/ may travel, by its path alone (both sides judge alike)."""
    parts = rel.split("/")
    if parts[0] in NEVER or parts[0] == "_claude" or rel.endswith(REMOTE_SUFFIX):
        return False
    if any(p in DERIVED or p.startswith(DERIVED_PREFIX) for p in parts[:-1]):
        return False
    if pathlib.PurePosixPath(rel).suffix.lower() not in TEXT and rel != ".dotlocalignore":
        return False
    prefixes = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
    return not any(fnmatch.fnmatch(p, pat.rstrip("/")) for pat in patterns for p in prefixes)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_files(local: pathlib.Path, patterns: list[str]):
    """Every file under .local/, skipping the folders nothing is taken from (and never walking them:
    a run's copies make .local/ gigabytes)."""
    if not local.is_dir():
        return
    for dirpath, dirs, files in os.walk(local):
        rel_dir = pathlib.Path(dirpath).relative_to(local).as_posix()
        keep = []
        for d in sorted(dirs):
            rel = d if rel_dir == "." else rel_dir + "/" + d
            if d in DERIVED or d.startswith(DERIVED_PREFIX) or (rel_dir == "." and d in NEVER):
                continue
            if any(fnmatch.fnmatch(rel, pat.rstrip("/")) for pat in patterns):
                continue
            keep.append(d)
        dirs[:] = keep
        for name in sorted(files):
            yield dirpath, name


def scan(place: Place) -> tuple[dict[str, str], set[str], list[str]]:
    """L: key → sha256 of what is here; the keys held back (too big, a link); warnings."""
    found: dict[str, str] = {}
    held: set[str] = set()
    warned: list[str] = []
    patterns = ignore_patterns(place)

    def take(key: str, path: pathlib.Path) -> None:
        if path.is_symlink():
            held.add(key)
            warned.append(f"skipped a symbolic link: {path}")
        elif path.stat().st_size > MAX_BYTES:
            held.add(key)
            warned.append(f"skipped, over {MAX_BYTES} bytes: {path}")
        else:
            found[key] = sha(path.read_bytes())

    for dirpath, name in local_files(place.local, patterns):
        rel = pathlib.Path(dirpath, name).relative_to(place.local).as_posix()
        if in_scope(rel, patterns):
            take("local/" + rel, pathlib.Path(dirpath) / name)
    if place.rules.is_file():
        take("claude/CLAUDE.md", place.rules)
    if place.memory.is_dir():
        for path in sorted(place.memory.rglob("*")):
            if path.is_file() or path.is_symlink():
                take("claude/memory/" + path.relative_to(place.memory).as_posix(), path)
    return found, held, warned


def pending_remote(place: Place) -> list[pathlib.Path]:
    out = [pathlib.Path(d, n) for d, n in local_files(place.local, ignore_patterns(place)) if n.endswith(REMOTE_SUFFIX)]
    if place.memory.is_dir():
        out += place.memory.rglob("*" + REMOTE_SUFFIX)
    if place.rules.parent.is_dir():
        out += place.rules.parent.glob(place.rules.name + REMOTE_SUFFIX)
    return sorted(out)


# --- gpg -------------------------------------------------------------------------------------

def gpg(args: list[str], data: bytes, passphrase: str) -> bytes:
    """gpg with the passphrase on a pipe of its own, never in argv."""
    r, w = os.pipe()
    os.write(w, passphrase.encode("utf-8") + b"\n")
    os.close(w)
    try:
        done = subprocess.run(["gpg", *GPG_COMMON, "--passphrase-fd", str(r), *args], input=data,
                              capture_output=True, timeout=GPG_TIMEOUT, pass_fds=(r,))
    except FileNotFoundError:
        raise Fault("gpg is not installed") from None
    finally:
        os.close(r)
    if done.returncode != 0:
        raise Fault("gpg failed (a wrong passphrase?): " + done.stderr.decode("utf-8", "replace").strip()[-300:])
    return done.stdout


def encrypt(data: bytes, passphrase: str) -> bytes:
    return gpg([*GPG_ENCRYPT, "--output", "-"], data, passphrase)


def decrypt(data: bytes, passphrase: str) -> bytes:
    return gpg(["--decrypt", "--output", "-"], data, passphrase)


# --- .local.asc/ -------------------------------------------------------------------------------

def remote_has_branch(place: Place) -> bool:
    done = git(["ls-remote", "--heads", place.remote, place.branch], place.root, check=False)
    if done.returncode != 0:
        raise Unreachable(f"cannot reach {place.remote or '(no remote)'}: " + done.stderr.strip()[-200:])
    return bool(done.stdout.strip())


def ready(place: Place) -> bool:
    """.local.asc/ as the remote has it; False when the remote branch does not exist yet."""
    if not place.remote:
        raise Unreachable("no origin to derive the dotlocal repository from; set DOTLOCAL_REMOTE")
    exists = remote_has_branch(place)
    if not (place.asc / ".git").is_dir():
        if exists:
            git(["clone", "--quiet", "--branch", place.branch, "--single-branch", place.remote, str(place.asc)], place.root)
        else:
            place.asc.mkdir(exist_ok=True)
            git(["init", "--quiet", "-b", place.branch], place.asc)
            git(["remote", "add", "origin", place.remote], place.asc)
        return exists
    if exists:
        git(["fetch", "--quiet", "origin", place.branch], place.asc)
        git(["reset", "--quiet", "--hard", "FETCH_HEAD"], place.asc)
        git(["clean", "-qfd"], place.asc)
    return exists


def read_base(place: Place) -> dict[str, str]:
    try:
        return json.loads(place.base_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_base(place: Place, manifest: dict[str, str]) -> None:
    tmp = place.base_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    os.replace(tmp, place.base_file)


def read_manifest(place: Place, passphrase: str) -> dict[str, str]:
    f = place.asc / MANIFEST
    if not f.is_file():
        return {}
    return json.loads(decrypt(f.read_bytes(), passphrase))


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".dotlocal-tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def identity(place: Place) -> list[str]:
    if git(["config", "user.email"], place.asc, check=False).stdout.strip():
        return []
    return ["-c", "user.name=dotlocal", "-c", "user.email=dotlocal@invalid"]


def commit_and_push(place: Place, message: str) -> bool:
    """Commit what .local.asc/ holds and push it; False when the remote moved first."""
    git(["add", "-A"], place.asc)
    if not git(["status", "--porcelain"], place.asc).stdout.strip():
        return True
    git([*identity(place), "commit", "--quiet", "-m", message], place.asc)
    done = git(["push", "--quiet", "origin", "HEAD:refs/heads/" + place.branch], place.asc, check=False)
    if done.returncode == 0:
        return True
    if "rejected" in done.stderr or "non-fast-forward" in done.stderr or "fetch first" in done.stderr:
        return False
    raise Fault("push to dotlocal failed: " + done.stderr.strip()[-300:])


# --- pull and push -----------------------------------------------------------------------------

def pull(place: Place, passphrase: str, out: list[str]) -> dict[str, str]:
    """Take the remote's changes; returns R. The manifest is read before any file is touched."""
    ready(place)
    remote = read_manifest(place, passphrase)  # a wrong passphrase stops here
    here, held, warned = scan(place)
    out += warned
    base = read_base(place)
    patterns = ignore_patterns(place)
    wrote = removed = clashed = 0
    for key in sorted(set(remote) | set(base)):
        if key in held or (key.startswith("local/") and not in_scope(key[len("local/"):], patterns)):
            continue
        r, b, h = remote.get(key), base.get(key), here.get(key)
        if r == b or h == r:
            continue
        path = place.plain(key)
        if h == b:
            if r is None:
                path.unlink(missing_ok=True)
                removed += 1
            else:
                data = decrypt(place.cipher(key).read_bytes(), passphrase)
                if sha(data) != r:
                    raise Fault(f"{key}: the ciphertext does not match the manifest; nothing more written")
                write_atomic(path, data)
                wrote += 1
        elif r is not None:
            data = decrypt(place.cipher(key).read_bytes(), passphrase)
            write_atomic(path.with_name(path.name + REMOTE_SUFFIX), data)
            clashed += 1
            out.append(f"both sides changed {path}: the other side's copy is {path.name}{REMOTE_SUFFIX}")
        else:
            out.append(f"the other side deleted {path}, changed here: kept")
    write_base(place, remote)
    out.append(f"pulled: {wrote} written, {removed} deleted, {clashed} in conflict")
    return remote


def push(place: Place, passphrase: str, out: list[str]) -> bool:
    """Pull, then send what differs; True when a commit went out."""
    for _attempt in range(3):
        remote = pull(place, passphrase, out)
        clashes = pending_remote(place)
        if clashes:
            raise Fault("settle these first (keep yours by deleting the copy): " + ", ".join(map(str, clashes)))
        here, held, _warned = scan(place)
        # a file held back (too big, a link) or no longer in scope keeps what the remote has: leaving
        # the allow-list stops a file travelling, it never deletes it on the other side
        patterns = ignore_patterns(place)
        manifest = dict(here)
        manifest.update({k: v for k, v in remote.items()
                         if k in held or (k.startswith("local/") and not in_scope(k[len("local/"):], patterns))})
        if manifest == remote:
            out.append("push: nothing changed")
            return False
        for key in sorted(set(remote) - set(manifest)):
            place.cipher(key).unlink(missing_ok=True)
        for key, digest in sorted(manifest.items()):
            if remote.get(key) != digest:
                write_atomic(place.cipher(key), encrypt(place.plain(key).read_bytes(), passphrase))
        write_atomic(place.asc / MANIFEST, encrypt(json.dumps(manifest, sort_keys=True).encode("utf-8"), passphrase))
        changed = sum(1 for k in set(manifest) | set(remote) if manifest.get(k) != remote.get(k))
        if commit_and_push(place, f"sync from {place.side} ({socket.gethostname()}): {changed} changed"):
            write_base(place, manifest)
            out.append(f"pushed: {changed} changed")
            return True
        out.append("the remote moved; pulling again")
    raise Fault("the remote kept moving; nothing pushed")


# --- the lock ----------------------------------------------------------------------------------

def lock_of(place: Place, ref: str = "HEAD") -> dict | None:
    done = git(["show", f"{ref}:{LOCK}"], place.asc, check=False)
    if done.returncode != 0:
        return None
    try:
        return json.loads(done.stdout)
    except ValueError:
        return None


def claim(place: Place, session: str, forced: bool) -> bool:
    """Write LOCK for this side and push it; False when the other side got there first."""
    for _attempt in range(2):
        ready(place)
        held = lock_of(place)
        if held and held.get("side") != place.side and not forced:
            return False
        if held and held.get("side") == place.side and not forced:
            return True
        record = {"side": place.side, "host": socket.gethostname(), "session": session,
                  "since": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "forced": forced}
        (place.asc / LOCK).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
        if commit_and_push(place, f"lock: {place.side}" + (" (forced)" if forced else "")):
            return True
    return False


def unlock(place: Place) -> None:
    ready(place)
    held = lock_of(place)
    if held and held.get("side") == place.side:
        (place.asc / LOCK).unlink()
        if not commit_and_push(place, f"unlock: {place.side}"):
            raise Fault("the remote moved while releasing the lock; run release again")


def branch_is_pushed(place: Place) -> list[str]:
    problems = []
    if git(["status", "--porcelain", "--untracked-files=no"], place.root).stdout.strip():
        problems.append("the working tree has changes not committed")
    upstream = git(["rev-parse", "--abbrev-ref", "@{u}"], place.root, check=False)
    if upstream.returncode != 0:
        problems.append("the branch has no upstream: push it first")
    elif git(["rev-list", "--count", "@{u}..HEAD"], place.root).stdout.strip() != "0":
        problems.append("the branch has commits not pushed")
    return problems


def deny(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def lock_check(place: Place) -> None:
    """PreToolUse: an edit, a write or a command goes through only on the side that holds the lock."""
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    command = str((event.get("tool_input") or {}).get("command", ""))
    if event.get("tool_name") == "Bash" and "dotlocal" in command:
        return
    if not (place.asc / ".git").is_dir():
        return
    stamp = place.asc / ".git" / "dotlocal-fetched"
    ref = "HEAD"
    try:
        if not stamp.exists() or time.time() - stamp.stat().st_mtime >= FETCH_EVERY:
            if git(["fetch", "--quiet", "origin", place.branch], place.asc, check=False, timeout=FETCH_TIMEOUT).returncode == 0:
                stamp.touch()
        # the newer of what was fetched and what this side pushed last (a claim is pushed from HEAD)
        if (git(["rev-parse", "--verify", "-q", "FETCH_HEAD"], place.asc, check=False).returncode == 0
                and git(["merge-base", "--is-ancestor", "FETCH_HEAD", "HEAD"], place.asc, check=False).returncode != 0):
            ref = "FETCH_HEAD"
    except subprocess.TimeoutExpired:
        pass
    held = lock_of(place, ref)
    if held and held.get("side") == place.side:
        return
    who = f"the {held['side']} side ({held.get('host', '?')}, since {held.get('since', '?')})" if held else "nobody"
    deny(f"dotlocal: {who} holds the lock of {place.branch}, so this side does not edit or run anything. "
         "Wait for `python3 tools/dotlocal.py release` there, or take it with "
         "`python3 tools/dotlocal.py take --force` typed in a terminal here.")


# --- hooks and the command line ----------------------------------------------------------------

def install(place: Place, out: list[str]) -> None:
    hooks = pathlib.Path(git(["rev-parse", "--git-path", "hooks"], place.root).stdout.strip())
    hooks = hooks if hooks.is_absolute() else place.root / hooks
    hook = hooks / "pre-push"
    if hook.exists():
        if HOOK_MARK not in hook.read_text(encoding="utf-8", errors="replace"):
            out.append(f"{hook} belongs to something else and was left alone; add to it: "
                       "python3 \"$(git rev-parse --show-toplevel)/tools/dotlocal.py\" push --from-hook || true")
        return
    hooks.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\n" + HOOK_MARK + " (tools/dotlocal.py)\n"
                    "python3 \"$(git rev-parse --show-toplevel)/tools/dotlocal.py\" push --from-hook </dev/null"
                    " || echo \"dotlocal: the sync failed; the push goes on\" >&2\nexit 0\n", encoding="utf-8")
    hook.chmod(0o755)
    out.append(f"installed {hook}")


def confirm_in_terminal(place: Place) -> bool:
    try:
        with open("/dev/tty", "r+", encoding="utf-8") as tty:
            tty.write(f"type the repository name ({place.branch}) to take the lock: ")
            tty.flush()
            return tty.readline().strip() == place.branch
    except OSError:
        return False


def rules_and_memory(place: Place) -> str:
    parts = []
    for title, path in (("Rules (~/.claude/CLAUDE.md)", place.rules), ("Memory index (MEMORY.md)", place.memory / "MEMORY.md")):
        if path.is_file():
            parts.append(f"## {title}\n\n" + path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def main(argv: list[str]) -> int:
    command = argv[0] if argv else "status"
    out: list[str] = []
    try:
        place = Place()
        passphrase = place.passphrase()
    except Fault as fault:
        if command in ("lock-check", "session-end"):
            return 0
        print(f"dotlocal: {fault}", file=sys.stderr)
        return 1 if command != "session-start" else 0
    if passphrase is None:
        return 0  # not set up here: a clone of the public repository is left alone
    try:
        if command == "lock-check":
            try:
                lock_check(place)
            except Exception as error:  # a broken check must not stop the work
                print(f"dotlocal lock-check: {error}", file=sys.stderr)
            return 0
        if command == "pull":
            pull(place, passphrase, out)
        elif command == "push":
            push(place, passphrase, out)
        elif command == "install":
            install(place, out)
        elif command == "session-start":
            install(place, out)
            pull(place, passphrase, out)
            if not claim(place, os.environ.get("CLAUDE_SESSION_ID", ""), forced=False):
                held = lock_of(place) or {}
                out.append(f"the {held.get('side', 'other')} side holds the lock: edits and commands are refused here "
                           "until it runs release, or `take --force` is typed in a terminal")
            if place.side == "cloud" or "--print-rules" in argv:
                out.append(rules_and_memory(place))
        elif command == "session-end":
            if not branch_is_pushed(place):
                push(place, passphrase, out)
                unlock(place)
        elif command == "release":
            problems = branch_is_pushed(place)
            if problems:
                raise Fault("not released: " + "; ".join(problems))
            push(place, passphrase, out)
            unlock(place)
            out.append("released")
        elif command == "take":
            if "--force" not in argv:
                raise Fault("take needs --force, and is typed in a terminal")
            if not confirm_in_terminal(place):
                raise Fault("not taken: the repository name was not typed in a terminal")
            if not claim(place, os.environ.get("CLAUDE_SESSION_ID", ""), forced=True):
                raise Fault("not taken: the remote moved; run it again")
            out.append(f"the lock is the {place.side} side's (forced)")
        elif command == "status":
            ready(place)
            remote = read_manifest(place, passphrase)
            here, held, warned = scan(place)
            differ = sorted(k for k in set(here) | set(remote) if k not in held and here.get(k) != remote.get(k))
            holder = lock_of(place)
            out.append(f"lock: {holder['side'] + ' (' + holder.get('host', '?') + ')' if holder else 'nobody'}")
            out.append(f"{len(here)} files here, {len(remote)} on the remote, {len(differ)} differ, {len(held)} held back")
            out += [f"  differs: {k}" for k in differ[:20]] + warned[:20]
        else:
            raise Fault("unknown command " + command)
    except Unreachable as fault:
        print(f"dotlocal: {fault}. In a cloud session, attach the dotlocal repository to the session; "
              ".local/ was not synced.")
        return 0 if command in ("session-start", "session-end") or "--from-hook" in argv else 1
    except (Fault, subprocess.TimeoutExpired, OSError, ValueError) as fault:
        text = f"dotlocal {command}: {fault}"
        if command in ("session-start", "session-end"):
            print(text)  # into the session's context, so the agent knows .local/ is not in step
            return 0
        print(text, file=sys.stderr)
        return 1
    if out:
        print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
