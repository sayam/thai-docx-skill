# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Every source file of this project says, in its first lines, whose it is and under which
licence (ADR 0003), as SPDX tags a tool can read: the skill's Python and JavaScript, the
tests and this project's own tools. Whoever writes a file names themself: one or more
`SPDX-FileCopyrightText` lines, any holder, then the licence. The two files that port
commonmark.js name its BSD-2-Clause licence and its author as well. The bundle drops each
part's tags and states every holder and licence once at its top. The verifiable-gates tools
keep the headers they were installed with."""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
# a holder: a year or years, then a name ("2026 Sayam Sriphua", "2026-2027 A Contributor <a@b.c>")
HOLDER = re.compile(r"SPDX-FileCopyrightText: \d{4}(?:[-–]\d{4})?(?:, \d{4}(?:[-–]\d{4})?)* \S.*")
MIT = "SPDX-License-Identifier: MIT"
# the Markdown parser ports commonmark.js 0.31.2 (skills/thai-docx/LICENSES/commonmark.js.txt)
PORT_HOLDER = "SPDX-FileCopyrightText: 2014 John MacFarlane"
PORT_LICENSE = "SPDX-License-Identifier: MIT AND BSD-2-Clause"
PORTS = {"js/40-markdown.js", "skills/thai-docx/scripts/thai_docx/markdown.py"}
BUNDLE = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx.js"


def sources() -> list[pathlib.Path]:
    installed = set(json.loads((ROOT / "tools" / "installed.json").read_text(encoding="utf-8"))["files"])
    groups = [
        sorted(ROOT.glob("js/*.js")),
        sorted((ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx").glob("*.py")),
        sorted(p for p in (ROOT / "tests").rglob("*.py") if "node_modules" not in p.parts),
        sorted((ROOT / "tests" / "js").glob("*.cjs")),
        sorted(p for p in (ROOT / "tools").glob("*.py") if p.relative_to(ROOT).as_posix() not in installed),
    ]
    assert all(groups), "a group of source files came back empty; the globs no longer match the tree"
    return [p for group in groups for p in group]


def spdx_head(path: pathlib.Path) -> list[str]:
    """The SPDX tags in the comment lines a file opens with, after a shebang if it has one."""
    prefix = "# " if path.suffix == ".py" else "// "
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    tags = []
    for line in lines:
        if not (line.startswith(prefix + "SPDX-")):
            break
        tags.append(line[len(prefix):])
    return tags


def head_is_right(tags: list[str], port: bool) -> bool:
    """At least one holder line, every holder line well formed, then exactly the licence line."""
    holders, licence = tags[:-1], tags[-1:]
    return (bool(holders) and all(HOLDER.fullmatch(h) for h in holders)
            and licence == [PORT_LICENSE if port else MIT]
            and (PORT_HOLDER in holders) is port)


def test_every_source_file_opens_with_its_copyright_and_licence():
    wrong = {}
    for path in sources():
        name = path.relative_to(ROOT).as_posix()
        if not head_is_right(spdx_head(path), name in PORTS):
            wrong[name] = spdx_head(path)
    assert not wrong, f"these files do not open with their SPDX lines: {wrong}"


def test_a_contributor_names_themself():
    """Any holder with a year is accepted; a line without a year or a name is not."""
    assert head_is_right(["SPDX-FileCopyrightText: 2027 A Contributor", MIT], port=False)
    two = ["SPDX-FileCopyrightText: 2026 Sayam Sriphua", "SPDX-FileCopyrightText: 2027-2028 B Contributor <b@example.org>", MIT]
    assert head_is_right(two, port=False)
    assert not head_is_right(["SPDX-FileCopyrightText: A Contributor", MIT], port=False)
    assert not head_is_right([MIT], port=False)


def test_the_bundle_states_its_parts_tags_once():
    holders, licences = [], []
    for path in sorted((ROOT / "js").glob("*.js")):
        for tag in spdx_head(path):
            key, value = tag.split(": ", 1)
            if key == "SPDX-License-Identifier":
                licences += [v for v in value.split(" AND ") if v not in licences]
            elif tag not in holders:
                holders.append(tag)
    text = BUNDLE.read_text(encoding="utf-8")
    assert spdx_head(BUNDLE) == holders + ["SPDX-License-Identifier: " + " AND ".join(licences)]
    assert text.count("SPDX-") == len(holders) + 1, "a part's SPDX lines reached the body of the bundle"
