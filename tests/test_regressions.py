# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A fault that was fixed stays fixed only while something fails when it returns.

`tests/regressions.yaml` names every finding closed since 0.2.0 and the test that holds it. A
row is held here to what its class promises: a test that exists, is collected, and is named in
full; a rule a person or a model reads only beside such a test; a check after the work only with
the record it is written in. A lesson written in prose and nothing else had already come back
once, in the review of 0.2.0, under a lesson that said so.

And the changelog: from the release after 0.2.0, every line under `### Fixed` names the test
that fails without the fix, so a fix is never announced on the word of the change alone.
"""

from __future__ import annotations

import ast
import pathlib
import re

from strictyaml import CommaSeparated, Enum, Map, Optional, Seq, Str, load

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "tests" / "regressions.yaml"
CHANGELOG = ROOT / "CHANGELOG.md"

CLASSES = ("C0", "C1", "C2", "C3")
FOUND_BY = ("review", "outside-review", "parity", "planted-input", "agent-run", "office-app")
SCHEMA = Seq(Map({
    "id": Str(),
    "what": Str(),
    "class": CommaSeparated(Enum(CLASSES)),
    "found_by": Enum(FOUND_BY),
    Optional("test"): Seq(Str()),
    Optional("record"): Str(),
}))
NODE = re.compile(r"(tests/[\w/]+\.py)::(test_\w+)")
# the last release whose Fixed lines were written before the rule
BEFORE_THE_RULE = "0.2.0"


def rows(text: str) -> list[dict]:
    return [{**row, "class": [str(c) for c in row["class"]]} for row in load(text, SCHEMA).data]


def functions_in(path: pathlib.Path) -> set[str]:
    """The test functions a module defines at its top level, as pytest collects them."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}


def faults(ledger: list[dict], root: pathlib.Path = ROOT) -> list[str]:
    out, seen = [], set()
    for row in ledger:
        name, classes, tests = row["id"], set(row["class"]), row.get("test", [])
        if name in seen:
            out.append(f"{name}: listed twice")
        seen.add(name)
        if not classes & {"C0", "C1"}:
            out.append(f"{name}: held by nothing that fails — a row needs C0 or C1")
        if classes & {"C0", "C1", "C2"} and not tests:
            out.append(f"{name}: {', '.join(sorted(classes))} names no test")
        if "C3" in classes and not row.get("record"):
            out.append(f"{name}: C3 names no record")
        if row.get("record") and not (root / row["record"]).is_file():
            out.append(f"{name}: record {row['record']} is not there")
        for node in tests:
            m = NODE.fullmatch(node)
            if m is None:
                out.append(f"{name}: '{node}' is not a test node id, file::function")
            elif not (root / m.group(1)).is_file() or m.group(2) not in functions_in(root / m.group(1)):
                out.append(f"{name}: {node} is not a test there is")
    return out


def unproven_fixes(changelog: str, root: pathlib.Path = ROOT) -> list[str]:
    """Lines under `### Fixed` in a section newer than 0.2.0 that name no test there is."""
    out = []
    for section in re.split(r"(?m)^## ", changelog)[1:]:
        heading = section.split("\n", 1)[0]
        if heading.startswith("[" + BEFORE_THE_RULE + "]"):
            break  # this release and the ones before it were written before the rule
        fixed = re.search(r"(?ms)^### Fixed\n(.*?)(?=^### |\Z)", section)
        for entry in re.split(r"(?m)^- ", fixed.group(1))[1:] if fixed else []:
            nodes = NODE.findall(entry)
            if not nodes or any(not (root / f).is_file() or t not in functions_in(root / f) for f, t in nodes):
                out.append(heading + ": " + entry.strip().split("\n", 1)[0][:80])
    return out


def test_every_fault_in_the_ledger_is_held_by_a_test_there_is():
    ledger = rows(LEDGER.read_text(encoding="utf-8"))
    assert len(ledger) >= 32, "the ledger parsed to almost nothing"
    assert faults(ledger) == []


def test_a_row_that_promises_what_it_does_not_hold_is_named(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_there():\n    pass\n", encoding="utf-8")
    ledger = rows(
        "- id: A\n  what: x\n  class: C2\n  found_by: review\n  test:\n    - tests/test_x.py::test_there\n"
        "- id: B\n  what: x\n  class: C1\n  found_by: review\n  test:\n    - tests/test_x.py::test_gone\n"
        "- id: C\n  what: x\n  class: C1, C3\n  found_by: office-app\n  test:\n    - tests/test_x.py::test_there\n"
        "- id: D\n  what: x\n  class: C1\n  found_by: review\n"
        "- id: A\n  what: x\n  class: C0\n  found_by: parity\n  test:\n    - tests/test_x.py\n"
    )
    assert faults(ledger, tmp_path) == [
        "A: held by nothing that fails — a row needs C0 or C1",
        "B: tests/test_x.py::test_gone is not a test there is",
        "C: C3 names no record",
        "D: C1 names no test",
        "A: listed twice",
        "A: 'tests/test_x.py' is not a test node id, file::function",
    ]


def test_every_fix_the_changelog_announces_names_its_test():
    assert unproven_fixes(CHANGELOG.read_text(encoding="utf-8")) == []


def test_a_fix_announced_without_its_test_is_named(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_there():\n    pass\n", encoding="utf-8")
    changelog = (
        "# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n"
        "- Held (`tests/test_x.py::test_there`).\n"
        "- Said, and held by nothing.\n"
        "- Held by a test that is gone (`tests/test_x.py::test_gone`).\n\n"
        "## [0.2.0] - 2026-09-24\n\n### Fixed\n\n- Written before the rule.\n"
    )
    assert unproven_fixes(changelog, tmp_path) == [
        "[Unreleased]: Said, and held by nothing.",
        "[Unreleased]: Held by a test that is gone (`tests/test_x.py::test_gone`).",
    ]
