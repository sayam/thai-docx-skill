# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Pack the skill for people who only use it: `skills/thai-docx/` as `thai-docx/` in
one zip, and nothing else from this repository (ADR 0018).

    python3 tools/package_skill.py OUT.zip          # write the archive
    python3 tools/package_skill.py --list           # the paths it would pack
    python3 tools/package_skill.py --tag v0.1.0     # exit 1 unless every version says 0.1.0 — the
                                                    # README and guides included — and the reading
                                                    # record of that version names every golden's bytes

The gates, tests and records stay in the repository, where a fork carries them. The
archive holds the files a client loads — the folder a skill upload expects — stored,
in path order, dated 1980-01-01, so the same tree gives the same bytes.

Role: generator (the archive) and decider (`--tag`).
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "thai-docx"


def files() -> list[pathlib.Path]:
    """The files git tracks under the skill directory: a file left there by hand — a note, a
    local profile, a cache — is not the skill, and never goes into a release."""
    listed = subprocess.run(["git", "ls-files", "-z", "--", SKILL.relative_to(ROOT).as_posix()],
                            cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    return sorted((ROOT / name for name in listed.split("\0") if name),
                  key=lambda p: p.relative_to(SKILL).as_posix())


def pack(out: pathlib.Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as zf:
        for path in files():
            info = zipfile.ZipInfo("thai-docx/" + path.relative_to(SKILL).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.create_system = 3  # as on Unix, whatever packs it
            zf.writestr(info, path.read_bytes())


def versions() -> dict[str, str]:
    """The version as each place that states it states it."""
    def text(path: pathlib.Path) -> str:
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    front = (text(SKILL / "SKILL.md").split("---", 2) + ["", ""])[1]
    found = {
        "SKILL.md metadata.version": re.search(r'^\s+version:\s*"([^"]+)"', front, re.M),
        "thai_docx.__version__": re.search(r'__version__ = "([^"]+)"', text(SKILL / "scripts" / "thai_docx" / "__init__.py")),
        "thai_docx.js VERSION": re.search(r'^const VERSION = "([^"]+)";', text(SKILL / "scripts" / "thai_docx.js"), re.M),
        "CHANGELOG.md newest release": re.search(r"^## \[(\d[^\]]*)\]", text(ROOT / "CHANGELOG.md"), re.M),
        "CITATION.cff version": re.search(r"^version: ['\"]?([^'\"\s]+)", text(ROOT / "CITATION.cff"), re.M),
    }
    return {k: (m.group(1) if m else "(missing)") for k, m in found.items()}


def dates() -> dict[str, str]:
    """The release date as each place that states it states it: the citation a reader copies
    must name the day the changelog says the release was made."""
    def text(path: pathlib.Path) -> str:
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    found = {
        "CHANGELOG.md newest release date": re.search(r"^## \[\d[^\]]*\] - (\d{4}-\d{2}-\d{2})", text(ROOT / "CHANGELOG.md"), re.M),
        "CITATION.cff date-released": re.search(r"^date-released: ['\"]?(\d{4}-\d{2}-\d{2})", text(ROOT / "CITATION.cff"), re.M),
    }
    return {k: (m.group(1) if m else "(missing)") for k, m in found.items()}


# PROMPT.th.md names the archive by hand too; PROMPT.md names no release, so it is not read here
INSTALL_PAGES = ["README.md", "PROMPT.th.md"] + [f"docs/guide/{lang}/{page}.md" for lang in ("en", "th") for page in ("install", "command-line")]
# the release an install page's commands fetch: the archive, its attestation bundle, the tag, the pin
INSTALL_VERSION = re.compile(r"thai-docx-(\d+\.\d+\.\d+)\.(?:zip|intoto)|refs/tags/v(\d+\.\d+\.\d+)|--pin v(\d+\.\d+\.\d+)")


def install_page_versions(root: pathlib.Path | None = None) -> dict[str, str]:
    """The release each install page's commands name, per page: one version, or every one it names
    joined by commas, or "(missing)". Written by hand at each release, so read at the tag."""
    root = root or ROOT
    out = {}
    for page in INSTALL_PAGES:
        path = root / page
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        found = sorted({next(g for g in m.groups() if g) for m in INSTALL_VERSION.finditer(text)})
        out[page] = ", ".join(found) or "(missing)"
    return out


def unread_goldens(version: str, root: pathlib.Path = ROOT) -> list[str]:
    """The goldens whose bytes the reading record of `version` does not name. A release is tagged
    on bytes read in the office applications (ADR 0012): its `what-vX.Y.Z-was-read-in` record names
    each golden's sha256. Between releases the goldens may move on `main`; a tag may not. The record
    is the one of the version tagged, not the newest file: a record of another version named the
    bytes it read, not these (the review of 0.3.0, F-12). A golden is named by a line that holds its
    file name and its sha256 both: a hash anywhere in the record let two goldens whose hashes were
    swapped pass as read (the reviews of 0.3.1)."""
    import hashlib
    records = sorted((root / "docs" / "evidence").glob("*-what-v" + version + "-was-read-in.md"))
    lines = [line for r in records for line in r.read_text(encoding="utf-8").splitlines()]
    return [g.name for g in sorted((root / "tests" / "golden").glob("*.docx"))
            if not any(g.name in line and hashlib.sha256(g.read_bytes()).hexdigest() in line for line in lines)]


def main(argv: list[str]) -> int:
    if argv == ["--list"]:
        for path in files():
            print("thai-docx/" + path.relative_to(SKILL).as_posix())
        return 0
    if len(argv) == 2 and argv[0] == "--tag":
        wanted = argv[1].removeprefix("v")
        found, days, pages = versions(), dates(), install_page_versions()
        wrong = {k: v for k, v in {**found, **pages}.items() if v != wanted}
        if len(set(days.values())) != 1 or "(missing)" in days.values():
            wrong.update(days)
        unread = unread_goldens(wanted)
        if unread:
            wrong["goldens no reading record names"] = ", ".join(unread)
        print(json.dumps({"tag": argv[1], "versions": found, "dates": days, "install pages": pages, "unread_goldens": unread, "ok": not wrong},
                         ensure_ascii=False))
        return 1 if wrong else 0
    if len(argv) == 1 and not argv[0].startswith("-"):
        pack(pathlib.Path(argv[0]))
        return 0
    print("usage: python3 tools/package_skill.py OUT.zip | --list | --tag vX.Y.Z", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
