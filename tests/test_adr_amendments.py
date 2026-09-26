# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""An amendment is recorded on both records: `Amends:` on the new one, `Amended by:` on the old.

`.github/CONTRIBUTING.md` asks for both sides, as it does for `Supersedes:`, but only the
supersession was read by anything — `adr-index-complete` checks it, from verifiable-gates,
installed and pinned by hash in `tools/installed.json`, so it is not changed here. The
amendment was read by nobody: in v0.2.0, 0004, 0022 and 0027 said they were amended by 0033,
0038 and 0039, and those three said nothing back (review of `b6dc363`, 2026-09-24, E4). The
links were made whole by hand; this holds them whole.

A field is read from a record's head — the lines above its first `##` heading — as a bullet
`- Amends:` or `- Amended by:` and the indented lines that continue it. The records it names
are the link texts `[NNNN](…)` in it; a number in its prose (*"cause 2"*) names nothing.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADR = ROOT / "docs" / "adr"

RECORD = re.compile(r"^(\d{4})-.*\.md$")
FIELD = re.compile(r"^- (Amends|Amended by):(.*)$", re.IGNORECASE)
CONTINUED = re.compile(r"^[ \t]+\S")
LINKED = re.compile(r"\[(\d{4})\]\(")


def fields(text: str) -> dict[str, set[str]]:
    """The records a head names under `Amends:` and under `Amended by:`."""
    found: dict[str, set[str]] = {"amends": set(), "amended by": set()}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            break
        if match := FIELD.match(line):
            current = match.group(1).lower()
            found[current].update(LINKED.findall(match.group(2)))
        elif current is not None and CONTINUED.match(line):
            found[current].update(LINKED.findall(line))
        else:
            current = None
    return found


def one_sided(adr_dir: pathlib.Path) -> list[str]:
    """Every amendment one record states and the other does not."""
    amends: dict[str, set[str]] = {}
    amended_by: dict[str, set[str]] = {}
    for path in sorted(adr_dir.glob("*.md")):
        if number := RECORD.match(path.name):
            head = fields(path.read_text(encoding="utf-8"))
            amends[number.group(1)] = head["amends"]
            amended_by[number.group(1)] = head["amended by"]
    problems = [
        f"{new} amends {old}, but {old} does not say it is amended by {new}"
        for new, olds in sorted(amends.items())
        for old in sorted(olds)
        if new not in amended_by.get(old, set())
    ]
    problems += [
        f"{old} is amended by {new}, but {new} does not say it amends {old}"
        for old, news in sorted(amended_by.items())
        for new in sorted(news)
        if old not in amends.get(new, set())
    ]
    return problems


def write(adr_dir: pathlib.Path, name: str, head: str) -> None:
    (adr_dir / name).write_text(f"# {name}\n\n- Status: accepted\n{head}\n## Where it came from\n\n", encoding="utf-8")


def test_every_amendment_in_this_project_is_recorded_on_both_records():
    assert one_sided(ADR) == []


def test_the_reader_finds_the_amendments_this_project_has():
    """A pattern that matches nothing would pass the test above on any tree."""
    pairs = {(new, old) for path in ADR.glob("*.md") if (n := RECORD.match(path.name))
             for new in [n.group(1)] for old in fields(path.read_text(encoding="utf-8"))["amends"]}
    assert {("0033", "0022"), ("0038", "0004"), ("0038", "0027"), ("0039", "0004"),
            ("0039", "0027"), ("0039", "0038")} <= pairs


def test_an_amendment_stated_on_one_record_only_is_named(tmp_path):
    write(tmp_path, "0001-old.md", "")
    write(tmp_path, "0002-new.md", "- Amends: [0001](0001-old.md) (what)\n")
    write(tmp_path, "0003-older.md", "- Amended by: [0004](0004-newer.md) (what)\n")
    write(tmp_path, "0004-newer.md", "")
    assert one_sided(tmp_path) == [
        "0002 amends 0001, but 0001 does not say it is amended by 0002",
        "0003 is amended by 0004, but 0004 does not say it amends 0003",
    ]


def test_a_field_continued_on_the_next_line_is_read_whole(tmp_path):
    write(tmp_path, "0001-old.md", "- Amended by: [0002](0002-a.md) (what),\n  [0003](0003-b.md) (what)\n")
    write(tmp_path, "0002-a.md", "- Amends: [0001](0001-old.md) (what)\n")
    write(tmp_path, "0003-b.md", "")
    assert one_sided(tmp_path) == ["0001 is amended by 0003, but 0003 does not say it amends 0001"]


def test_a_number_in_the_prose_or_below_the_head_names_no_record(tmp_path):
    write(tmp_path, "0001-old.md", "- Amended by: [0002](0002-new.md) cause 0003, which read *0004*\n")
    write(tmp_path, "0002-new.md", "- Amends: [0001](0001-old.md)\n- Extends: [0003](0003-x.md)\n")
    (tmp_path / "0002-new.md").write_text(
        (tmp_path / "0002-new.md").read_text(encoding="utf-8") + "- Amends: [0005](0005-y.md)\n",
        encoding="utf-8",
    )
    assert one_sided(tmp_path) == []
