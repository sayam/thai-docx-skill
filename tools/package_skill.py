# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Pack the skill for people who only use it: `skills/thai-docx/` as `thai-docx/` in
one zip, and nothing else from this repository (ADR 0018).

    python3 tools/package_skill.py OUT.zip          # write the archive
    python3 tools/package_skill.py --list           # the paths it would pack
    python3 tools/package_skill.py --tag v0.1.0     # exit 1 unless every version says 0.1.0

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


def main(argv: list[str]) -> int:
    if argv == ["--list"]:
        for path in files():
            print("thai-docx/" + path.relative_to(SKILL).as_posix())
        return 0
    if len(argv) == 2 and argv[0] == "--tag":
        wanted = argv[1].removeprefix("v")
        found, days = versions(), dates()
        wrong = {k: v for k, v in found.items() if v != wanted}
        if len(set(days.values())) != 1 or "(missing)" in days.values():
            wrong.update(days)
        print(json.dumps({"tag": argv[1], "versions": found, "dates": days, "ok": not wrong}, ensure_ascii=False))
        return 1 if wrong else 0
    if len(argv) == 1 and not argv[0].startswith("-"):
        pack(pathlib.Path(argv[0]))
        return 0
    print(__doc__.strip().splitlines()[2].strip() + " | --list | --tag vX.Y.Z", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
