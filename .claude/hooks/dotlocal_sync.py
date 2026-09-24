#!/usr/bin/env python3
"""Keep .local/ (plaintext, git-ignored) in step with a private repo that only ever sees ciphertext.

Layout, relative to the repository root:

    .local/                 plaintext; ignored by this repository's git
    .local.asc/             a clone of the dotlocal repo, one branch per project repository;
                            every file of .local/ sits at the same path with ".asc" appended,
                            OpenPGP-armored and symmetrically encrypted (AES-256) by gpg
    .local.asc/.dotlocal-manifest.asc
                            the sha256 of every plaintext file, itself encrypted, so that what
                            changed is decided without decrypting every file and without the
                            hashes of short files being readable on GitHub

gpg makes a new ciphertext every time it encrypts, so the ciphertext cannot be compared. What is
compared is the sha256 of the plaintext, three ways:

    L   the files in .local/ now
    B   the manifest as it stood at the last sync on this machine (.local.asc/.git/dotlocal-base.json)
    R   the manifest on the remote branch

    pull  for each path: L == B and R != B  -> write R's file (or delete it) into .local/
                         R == B              -> a local change; left for push
                         L != B != R != L    -> a conflict: .local/ keeps its file and the remote
                                                one is written beside it as <name>.dotlocal-remote;
                                                push refuses to run until those are deleted
    push  pull, then encrypt each path whose L differs from R, remove what .local/ no longer has,
          commit and push; a push the remote rejects is retried from a fresh pull

When they run: pull from Claude Code's SessionStart hook (.claude/settings.json); push from git's
pre-push hook, so .local/ goes up once per `git push` of this repository, whoever runs it. pull
installs that pre-push hook, unless a pre-push hook of some other origin is already there. A failed
sync never stops the git push; it says why on stderr.

.local.asc/ is derived state: pull resets it to the remote branch, so a commit that never got pushed
is rebuilt from .local/ on the next push rather than merged.

Configuration, all from the environment:

    DOTLOCAL_PASSPHRASE       the passphrase; or
    DOTLOCAL_PASSPHRASE_FILE  a file holding it (default ~/.config/dotlocal/passphrase)
    DOTLOCAL_REMOTE           default: this repository's origin URL with the name replaced by "dotlocal"
    DOTLOCAL_BRANCH           default: this repository's name

With no passphrase the hook does nothing and exits 0, so a clone without one is unaffected.
Paths in .local/.dotlocalignore (fnmatch patterns, one per line, # for comments) are never synced.

Usage: dotlocal_sync.py pull | push | status | install
"""

import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = ".dotlocal-manifest.asc"
IGNORE_FILE = ".dotlocalignore"
REMOTE_COPY = ".dotlocal-remote"
TMP_PREFIX = ".dotlocal-tmp-"
PUSH_ATTEMPTS = 3
HOOK_MARK = "# installed by .claude/hooks/dotlocal_sync.py"
PRE_PUSH = f"""#!/bin/sh
{HOOK_MARK}
# Encrypts .local/ and pushes it to the dotlocal repo; never blocks this push.
top=$(git rev-parse --show-toplevel)
script="$top/.claude/hooks/dotlocal_sync.py"
[ -f "$script" ] && python3 "$script" push </dev/null
exit 0
"""


class SyncError(Exception):
    pass


def log(msg):
    print(f"dotlocal: {msg}", file=sys.stderr)


def git(*args, cwd, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise SyncError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def project_root():
    start = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(git("rev-parse", "--show-toplevel", cwd=start).stdout.strip())


def passphrase():
    if os.environ.get("DOTLOCAL_PASSPHRASE"):
        return os.environ["DOTLOCAL_PASSPHRASE"]
    f = Path(os.environ.get("DOTLOCAL_PASSPHRASE_FILE") or Path.home() / ".config/dotlocal/passphrase")
    if f.is_file():
        return f.read_text().rstrip("\r\n")
    return None


def remote_and_branch(root):
    origin = git("remote", "get-url", "origin", cwd=root).stdout.strip()
    name = re.sub(r"\.git$", "", origin.rstrip("/")).rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    remote = os.environ.get("DOTLOCAL_REMOTE") or re.sub(r"[^/:]+?(\.git)?/?$", r"dotlocal\1", origin)
    return remote, os.environ.get("DOTLOCAL_BRANCH") or name


class Gpg:
    def __init__(self, secret):
        self.secret = secret.encode()

    def _run(self, *args):
        rfd, wfd = os.pipe()
        os.write(wfd, self.secret)
        os.close(wfd)
        try:
            r = subprocess.run(
                ["gpg", "--batch", "--yes", "--quiet", "--no-symkey-cache", "--pinentry-mode", "loopback",
                 "--passphrase-fd", str(rfd), *args],
                pass_fds=(rfd,), capture_output=True)
        finally:
            os.close(rfd)
        if r.returncode:
            raise SyncError(f"gpg {args[-1]}: {r.stderr.decode(errors='replace').strip()}")
        return r.stdout

    def encrypt(self, src, dst):
        # --rfc4880 keeps the packets readable by gpg 2.2 (RHEL 8/9); 2.4 would otherwise write OCB.
        self._run("--rfc4880", "--symmetric", "--cipher-algo", "AES256", "--s2k-digest-algo", "SHA512", "--armor", "--output", str(dst), str(src))

    def decrypt(self, src, dst):
        self._run("--output", str(dst), "--decrypt", str(src))

    def decrypt_bytes(self, src):
        return self._run("--output", "-", "--decrypt", str(src))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ignore_patterns(plain):
    f = plain / IGNORE_FILE
    if not f.is_file():
        return []
    return [ln.strip() for ln in f.read_text().splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def scan(plain):
    """sha256 of every regular file under .local/, keyed by its path relative to .local/."""
    if not plain.is_dir():
        return {}
    patterns = ignore_patterns(plain)
    out = {}
    for dirpath, dirnames, filenames in os.walk(plain):
        dirnames.sort()
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            rel = p.relative_to(plain).as_posix()
            if fn.endswith(REMOTE_COPY) or fn.startswith(TMP_PREFIX):
                continue
            if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(fn, pat) for pat in patterns):
                continue
            if p.is_symlink() or not p.is_file():
                log(f"skipped {rel}: not a regular file")
                continue
            out[rel] = sha256(p)
    return out


def pending_conflicts(plain):
    if not plain.is_dir():
        return []
    return sorted(p.relative_to(plain).as_posix() for p in plain.rglob(f"*{REMOTE_COPY}"))


class Sync:
    def __init__(self, root, gpg):
        self.root = root
        self.plain = root / ".local"
        self.enc = root / ".local.asc"
        self.gpg = gpg
        self.remote, self.branch = remote_and_branch(root)
        self.base_file = self.enc / ".git" / "dotlocal-base.json"

    # --- the encrypted clone -------------------------------------------------------------

    def remote_has_branch(self):
        r = git("ls-remote", "--exit-code", "--heads", self.remote, self.branch, cwd=self.root, check=False)
        if r.returncode not in (0, 2):
            raise SyncError(f"cannot reach {self.remote}: {r.stderr.strip()}")
        return r.returncode == 0

    def ensure_clone(self):
        if (self.enc / ".git").is_dir():
            return
        if self.enc.exists() and any(self.enc.iterdir()):
            raise SyncError(f"{self.enc} exists and is not a git clone; move it aside")
        self.enc.mkdir(exist_ok=True)
        git("init", "-q", cwd=self.enc)
        git("remote", "add", "origin", self.remote, cwd=self.enc)
        git("checkout", "-q", "--orphan", self.branch, cwd=self.enc)

    def fetch(self):
        """Reset .local.asc/ to the remote branch; False when the branch does not exist yet."""
        if not self.remote_has_branch():
            return False
        git("fetch", "-q", "origin", f"+refs/heads/{self.branch}:refs/remotes/origin/{self.branch}", cwd=self.enc)
        git("checkout", "-q", "-B", self.branch, f"origin/{self.branch}", cwd=self.enc)
        git("reset", "-q", "--hard", f"origin/{self.branch}", cwd=self.enc)
        git("clean", "-qfdx", cwd=self.enc)
        return True

    def remote_manifest(self):
        f = self.enc / MANIFEST
        return json.loads(self.gpg.decrypt_bytes(f)) if f.is_file() else {}

    def load_base(self):
        return json.loads(self.base_file.read_text()) if self.base_file.is_file() else {}

    def save_base(self, m):
        self.base_file.write_text(json.dumps(m, indent=0, sort_keys=True))

    # --- plaintext side ------------------------------------------------------------------

    def write_plain(self, rel, dst):
        src = self.enc / f"{rel}.asc"
        dst.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=TMP_PREFIX, dir=dst.parent)
        os.close(fd)
        try:
            self.gpg.decrypt(src, tmp)
            os.replace(tmp, dst)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def remove_plain(self, rel):
        p = self.plain / rel
        p.unlink(missing_ok=True)
        prune_empty(p.parent, self.plain)

    # --- commands ------------------------------------------------------------------------

    def pull(self):
        self.ensure_clone()
        self.fetch()
        R = self.remote_manifest()
        B = self.load_base()
        L = scan(self.plain)
        taken, removed, conflicts = [], [], []
        for rel in sorted(set(R) | set(B) | set(L)):
            r, b, l_ = R.get(rel), B.get(rel), L.get(rel)
            if r == l_ or r == b:
                continue  # already equal, or only .local/ changed (push sends it)
            if l_ == b:
                if r is None:
                    self.remove_plain(rel)
                    removed.append(rel)
                else:
                    self.write_plain(rel, self.plain / rel)
                    taken.append(rel)
            elif r is None:
                conflicts.append(f"{rel} (deleted remotely, changed here: kept)")
            elif l_ is None:
                self.write_plain(rel, self.plain / rel)
                conflicts.append(f"{rel} (changed remotely, deleted here: restored)")
            else:
                self.write_plain(rel, self.plain / f"{rel}{REMOTE_COPY}")
                conflicts.append(f"{rel} (changed on both sides: remote copy in {rel}{REMOTE_COPY})")
        self.save_base(R)
        return taken, removed, conflicts

    def push(self):
        for attempt in range(1, PUSH_ATTEMPTS + 1):
            self.pull()
            waiting = pending_conflicts(self.plain)
            if waiting:
                raise SyncError("resolve and delete these before pushing: " + ", ".join(waiting))
            R = self.load_base()
            L = scan(self.plain)
            changed = [rel for rel in sorted(L) if L[rel] != R.get(rel)]
            gone = [rel for rel in sorted(R) if rel not in L]
            if not changed and not gone:
                return [], []
            for rel in changed:
                dst = self.enc / f"{rel}.asc"
                dst.parent.mkdir(parents=True, exist_ok=True)
                self.gpg.encrypt(self.plain / rel, dst)
            for rel in gone:
                dst = self.enc / f"{rel}.asc"
                dst.unlink(missing_ok=True)
                prune_empty(dst.parent, self.enc)
            self.write_manifest(L)
            git("add", "-A", cwd=self.enc)
            where = "cloud" if os.environ.get("CLAUDE_CODE_REMOTE") else platform.node()
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            git("commit", "-q", "-m", f"sync from {where} at {stamp}: {len(changed)} changed, {len(gone)} removed", cwd=self.enc)
            r = git("push", "-q", "origin", f"HEAD:refs/heads/{self.branch}", cwd=self.enc, check=False)
            if r.returncode == 0:
                self.save_base(L)
                return changed, gone
            log(f"push rejected (attempt {attempt}/{PUSH_ATTEMPTS}): {r.stderr.strip()}")
        raise SyncError("push kept being rejected; .local/ is unchanged and will be pushed next time")

    def write_manifest(self, m):
        fd, tmp = tempfile.mkstemp(prefix=TMP_PREFIX)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(m, f, indent=0, sort_keys=True)
            self.gpg.encrypt(tmp, self.enc / MANIFEST)
        finally:
            os.unlink(tmp)

    def status(self):
        B = self.load_base()
        L = scan(self.plain)
        for rel in sorted(set(B) | set(L)):
            if B.get(rel) != L.get(rel):
                print(("A " if rel not in B else "D " if rel not in L else "M ") + rel)
        for rel in pending_conflicts(self.plain):
            print("C " + rel)


def install_pre_push(root):
    hook = Path(git("rev-parse", "--git-path", "hooks/pre-push", cwd=root).stdout.strip())
    hook = hook if hook.is_absolute() else root / hook
    if hook.is_file():
        if HOOK_MARK not in hook.read_text(errors="replace"):
            log(f"{hook} exists and is not ours; add `python3 .claude/hooks/dotlocal_sync.py push` to it by hand")
            return
        if hook.read_text() == PRE_PUSH:
            return
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(PRE_PUSH)
    hook.chmod(0o755)


def prune_empty(d, stop):
    while d != stop and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def main(argv):
    if len(argv) != 2 or argv[1] not in ("pull", "push", "status", "install"):
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 64
    if not sys.stdin.isatty():
        sys.stdin.read()  # the hook's JSON event; nothing in it is needed
    secret = passphrase()
    if secret is None:
        log("no DOTLOCAL_PASSPHRASE or passphrase file; skipped")
        return 0
    if shutil.which("gpg") is None:
        log("gpg is not installed; skipped")
        return 1
    try:
        root = project_root()
        if argv[1] in ("pull", "install"):
            install_pre_push(root)
        if argv[1] == "install":
            return 0
        s = Sync(root, Gpg(secret))
        if argv[1] == "status":
            s.status()
        elif argv[1] == "pull":
            taken, removed, conflicts = s.pull()
            if taken or removed:
                print(f"dotlocal: pulled {len(taken)} file(s), removed {len(removed)} from .local/")
            for c in conflicts:
                print(f"dotlocal: CONFLICT {c}")
        else:
            changed, gone = s.push()
            if changed or gone:
                log(f"pushed {len(changed)} changed, {len(gone)} removed to {s.branch}")
    except SyncError as e:
        log(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
