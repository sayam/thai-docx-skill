# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The mutant list is well formed, the workflows run it, and the runner gives the verdicts it says.

A C1 test is one shown to fail on a mutant of the code (ADR 0041). The showing was made once, by
hand, when each fix was made, and nothing made it again: a test weakened later, or code moved from
under it, passed every gate green. `tools/mutants.yaml` writes each showing down and
`tools/run_mutants.py` makes it on every pull request and at the tag. This holds the list to its
shape before that run reads it, holds the two workflows to running it, and plants on a small tree
each defect the runner must name: a mutant that survives, a change found nowhere or twice, one that
does not compile, a test that is not there or did not run, a control that is not there, a file git
does not track.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_mutants as rm  # noqa: E402

ROWS = rm.rows((ROOT / rm.LIST).read_text(encoding="utf-8"))
MUTANTS_STEP = "python3 tools/run_mutants.py"
COVERAGE_STEP = "python3 -W error -m coverage combine -q && python3 -m coverage report"


def test_every_row_of_the_list_is_well_formed():
    assert len(ROWS) >= 40, "the list parsed to almost nothing"
    ids = [row["id"] for row in ROWS]
    assert len(set(ids)) == len(ids), "a mutant is listed twice"
    known = rm.controls(ROOT)
    assert {row["id"]: rm.faults(row, ROOT, known) for row in ROWS if rm.faults(row, ROOT, known)} == {}
    # every test file the list points at is one the gate index claims, and the goldens are not touched
    assert all(not row["file"].startswith("tests/golden/") for row in ROWS)


def test_the_list_runs_on_every_pull_request_and_at_the_tag():
    """The run belongs where the suite runs: after the coverage report in the `tests` job of
    gates.yml, and in `release-check`, so a mutant that survives is seen before a tag — a pushed
    tag cannot be moved. `tests-newest` does not run it: the list measures the tests, not the
    runtime."""
    for workflow, job in (("gates.yml", "tests"), ("release.yml", "release-check")):
        jobs = yaml.safe_load((ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8"))["jobs"]
        steps = [str(step.get("run", "")) for step in jobs[job]["steps"] if "if" not in step]
        assert MUTANTS_STEP in steps, (workflow, job)
        assert steps.index(MUTANTS_STEP) > steps.index(COVERAGE_STEP), (workflow, job)
        others = [name for name, other in jobs.items() if name != job and MUTANTS_STEP in [str(s.get("run", "")) for s in other["steps"]]]
        assert others == [], (workflow, others)


# --- the runner, on a tree of its own ------------------------------------------------------------


def tree(tmp_path: pathlib.Path) -> pathlib.Path:
    """A git working tree of a package, its tests, a ledger and a gate index — and one file git
    does not track."""
    root = tmp_path / "tree"
    for folder in ("pkg", "tests", "tools"):
        (root / folder).mkdir(parents=True)
    (root / "pkg" / "limits.py").write_text("CAP = 40\nOTHER = 1\nOTHER = 1\n", encoding="utf-8")
    (root / "pkg" / "data.json").write_text('{"cap": 40}\n', encoding="utf-8")
    (root / "tests" / "conftest.py").write_text(
        "import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))\n", encoding="utf-8")
    (root / "tests" / "test_limits.py").write_text(
        "import json, pathlib\nimport pytest\nfrom pkg import limits\n\n"
        "def test_cap():\n    assert limits.CAP == 40\n\n"
        "def test_other():\n    assert limits.OTHER == 1\n\n"
        "def test_data():\n    assert json.loads((pathlib.Path(__file__).parent.parent / 'pkg' / 'data.json').read_text())['cap'] == 40\n\n"
        "def test_skipped():\n    pytest.skip('not here')\n",
        encoding="utf-8")
    (root / "tests" / "regressions.yaml").write_text(
        "- id: L-1\n  what: x\n  class: C1\n  found_by: review\n  test:\n    - tests/test_limits.py::test_cap\n", encoding="utf-8")
    (root / "gates.yaml").write_text(
        "version: 1\ngates:\n  - id: g-1\n    title: t\n    kind: test\n    severity: blocking\n"
        "    enforced_by: {job: tests, tests: [tests/test_limits.py]}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)  # the index is what ls-files reads
    (root / "pkg" / "untracked.py").write_text("CAP = 40\n", encoding="utf-8")
    return root


def row(id: str, file: str = "pkg/limits.py", find: str = "CAP = 40", replace: str = "CAP = 400",
        test: str = "tests/test_limits.py::test_cap", holds: str = "L-1") -> dict:
    return {"id": id, "file": file, "find": find, "replace": replace, "test": [test], "holds": [holds]}


def test_each_defect_of_a_row_or_of_the_runner_is_named(tmp_path):
    root = tree(tmp_path)
    planted = [
        row("killed"),
        row("killed-by-the-gate-it-holds", holds="g-1"),
        row("survives", replace="CAP = 40 + 0"),
        row("find-nowhere", find="CAP = 41"),
        row("find-twice", find="OTHER = 1", replace="OTHER = 2", test="tests/test_limits.py::test_other"),
        row("no-compile", replace="CAP = = 400"),
        row("no-compile-json", file="pkg/data.json", find='{"cap": 40}', replace='{"cap": 40', test="tests/test_limits.py::test_data"),
        row("no-compile-yaml", file="gates.yaml", find="version: 1", replace="version: [1", test="tests/test_limits.py::test_cap"),
        row("test-gone", test="tests/test_limits.py::test_gone"),
        row("not-a-node-id", test="tests/test_limits.py"),
        row("test-skipped", test="tests/test_limits.py::test_skipped"),
        row("holds-nothing-there", holds="L-9"),
        row("same-text", replace="CAP = 40"),
        row("untracked", file="pkg/untracked.py"),
        row("file-gone", file="pkg/gone.py"),
    ]
    said = []
    outcomes = rm.run(root, planted, say=said.append)
    assert [(o.id, o.status) for o in outcomes] == [
        ("killed", "killed"), ("killed-by-the-gate-it-holds", "killed"), ("survives", "survived"), ("find-nowhere", "broken"),
        ("find-twice", "broken"), ("no-compile", "broken"), ("no-compile-json", "broken"), ("no-compile-yaml", "broken"),
        ("test-gone", "broken"), ("not-a-node-id", "broken"), ("test-skipped", "broken"), ("holds-nothing-there", "broken"),
        ("same-text", "broken"), ("untracked", "broken"), ("file-gone", "broken"),
    ]
    why = {o.id: o.why for o in outcomes}
    assert why["killed"] == "" and why["killed-by-the-gate-it-holds"] == ""
    assert why["survives"].startswith("the test passed on the mutant:") and "1 passed" in why["survives"]
    assert why["find-nowhere"] == "find is in pkg/limits.py 0 times, not once"
    assert why["find-twice"] == "find is in pkg/limits.py 2 times, not once"
    assert why["no-compile"].startswith("pkg/limits.py does not compile: invalid syntax")
    assert why["no-compile-json"].startswith("pkg/data.json does not compile:")
    assert why["no-compile-yaml"].startswith("gates.yaml does not compile:")
    assert why["test-gone"] == "tests/test_limits.py::test_gone is not a test there is"
    assert why["not-a-node-id"] == "'tests/test_limits.py' is not a test node id, file::function"
    assert why["test-skipped"].startswith("no test ran (skipped, or nothing collected):") and "1 skipped" in why["test-skipped"]
    assert why["holds-nothing-there"] == "holds L-9, which is neither a ledger row nor a gate"
    assert why["same-text"] == "find and replace are the same text: no mutant"
    assert why["untracked"] == "pkg/untracked.py is not tracked by git"
    assert why["file-gone"] == "pkg/gone.py is not a file there is"
    # one line per mutant, the reason under it, and nothing was changed in the tree itself
    assert [line.split()[0] for line in said if not line.startswith(" ")] == [o.status for o in outcomes]
    assert (root / "pkg" / "limits.py").read_text(encoding="utf-8") == "CAP = 40\nOTHER = 1\nOTHER = 1\n"
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout
    assert status.splitlines() and all(line.startswith(("A  ", "?? ")) for line in status.splitlines()), status


def test_the_command_counts_everything_and_passes_only_when_every_mutant_is_killed(tmp_path, capsys):
    root = tree(tmp_path)
    listed = root / "tools" / "mutants.yaml"
    def listed_row(id: str, find: str, replace: str) -> str:
        return (f"- id: {id}\n  file: pkg/limits.py\n  find: {find}\n  replace: {replace}\n"
                "  test:\n    - tests/test_limits.py::test_cap\n  holds:\n    - L-1\n")

    listed.write_text(listed_row("killed", "CAP = 40", "CAP = 400") + listed_row("survives", "CAP = 40", "CAP = 40 + 0")
                      + listed_row("broken", "CAP = 41", "CAP = 400"), encoding="utf-8")
    assert rm.main(["--root", str(root)]) == 1
    out = capsys.readouterr().out
    assert out.rstrip().splitlines()[-1].startswith("3 mutants: 1 killed, 1 survived, 1 broken (")
    assert rm.main(["--root", str(root), "--only", "killed"]) == 0
    assert capsys.readouterr().out.rstrip().splitlines()[-1].startswith("1 mutants: 1 killed, 0 survived, 0 broken (")
    assert rm.main(["--root", str(root), "--only", "nobody"]) == 2
    assert "no row is named nobody" in capsys.readouterr().err
    listed.write_text("", encoding="utf-8")
    assert rm.main(["--root", str(root)]) == 1, "an empty list kills nothing"
