# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Every mutant in tools/mutants.yaml is killed by the test it names, or this exits 1.

    python3 tools/run_mutants.py              # the whole list
    python3 tools/run_mutants.py --only ID    # one row, while it is being written

A C1 test is one shown to fail — on the code before the fix, or on a mutant of the code after it
(ADR 0041). That showing was done once, by hand, when the fix was made, and nothing did it again:
a test weakened later, or code moved from under it, passed green on every pull request. A row of
tools/mutants.yaml is that showing written down — one change to one tracked file, found exactly
once, and the test that must fail on it — and this runs every row on every pull request and at
the tag.

For each row the tracked files (`git ls-files`; never `git archive`, whose export-ignore leaves
js/, tests/ and CITATION.cff out) are copied to a directory of their own, tests/js/node_modules is
linked in, the change is made in the copy, and the changed file is compiled — a .py through
`compile()`, a part under js/ or an asset by rebuilding the bundle there and `node --check` on
it, JSON and YAML by parsing — because a mutant that does not compile fails its test for the
wrong reason and would count as killed. Then `python3 -B -m pytest -q -x -p no:cacheprovider` runs
the named tests in the copy, a fresh copy for every row, so no cache of the last row's bytes is
read.

pytest exit 1 is a kill. Exit 0 is a mutant that survived — the test no longer bites — and the
run fails. Any other exit (a collection error, a usage error, no test collected), and a test that
only skipped, is a broken row, and the run fails. So is a row whose compiling or whose tests run
past TIMEOUT_SECONDS: it is stopped and named, where a job that ran into its own limit would name
nothing. A `find` found nowhere or twice, a test or a control that does not exist, is a broken row
too, named before anything runs. The last line counts all of it: total = killed + survived + broken.

Role: decider — exit 0 only when every row is killed.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

import yaml
from strictyaml import Map, Seq, Str, load

__all__ = ["Outcome", "controls", "faults", "main", "rows", "run"]

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIST = pathlib.Path("tools") / "mutants.yaml"
LEDGER = pathlib.Path("tests") / "regressions.yaml"
GATES = pathlib.Path("gates.yaml")
BUNDLE = pathlib.Path("skills") / "thai-docx" / "scripts" / "thai_docx.js"
BUNDLER = pathlib.Path("tools") / "bundle_js.py"
# a change here changes the bundle too, so the bundle is rebuilt before the tests read it
BUNDLED = ("js/", "skills/thai-docx/assets/")
NODE_MODULES = pathlib.Path("tests") / "js" / "node_modules"
NODE = re.compile(r"(tests/[\w/]+\.py)::(test_\w+)")
SCHEMA = Seq(Map({"id": Str(), "file": Str(), "find": Str(), "replace": Str(), "test": Seq(Str()), "holds": Seq(Str())}))
PYTEST = [sys.executable, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"]
# one row's tests, and one rebuild of the bundle: the slowest row takes a minute on a slow machine,
# and a row that hangs is stopped and named long before the job's own limit
TIMEOUT_SECONDS = 180


@dataclasses.dataclass
class Outcome:
    id: str
    status: str  # killed · survived · broken
    seconds: float
    why: str = ""


def rows(text: str) -> list[dict]:
    """The list, as data; a row outside the schema stops here with strictyaml's own words."""
    if not text.strip():
        return []
    return [dict(row) for row in load(text, SCHEMA).data]


def controls(root: pathlib.Path) -> set[str]:
    """Every id a row's `holds` may name: the ledger's and the gate index's."""
    ledger = yaml.safe_load((root / LEDGER).read_text(encoding="utf-8")) or []
    gates = yaml.safe_load((root / GATES).read_text(encoding="utf-8")) or {}
    return {str(row["id"]) for row in ledger} | {str(gate["id"]) for gate in gates.get("gates", [])}


def functions_in(path: pathlib.Path) -> set[str]:
    """The test functions a module defines at its top level, as pytest collects them."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}


def faults(row: dict, root: pathlib.Path, known: set[str] | None = None) -> list[str]:
    """What is wrong with one row before it runs — empty means it can run."""
    out = []
    path = root / row["file"]
    if not path.is_file():
        out.append(f"{row['file']} is not a file there is")
    else:
        found = path.read_text(encoding="utf-8").count(row["find"])
        if found != 1:
            out.append(f"find is in {row['file']} {found} times, not once")
    if row["find"] == row["replace"]:
        out.append("find and replace are the same text: no mutant")
    if not row["test"]:
        out.append("names no test")
    for node in row["test"]:
        m = NODE.fullmatch(node)
        if m is None:
            out.append(f"'{node}' is not a test node id, file::function")
        elif not (root / m.group(1)).is_file() or m.group(2) not in functions_in(root / m.group(1)):
            out.append(f"{node} is not a test there is")
    if not row["holds"]:
        out.append("holds nothing: a row names the ledger row or the gate it holds")
    for held in row["holds"]:
        if held not in (controls(root) if known is None else known):
            out.append(f"holds {held}, which is neither a ledger row nor a gate")
    return out


def _copy(root: pathlib.Path) -> pathlib.Path:
    """The tracked files, and nothing else, in a directory of their own."""
    names = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True,
                           timeout=TIMEOUT_SECONDS).stdout.decode("utf-8", "surrogateescape")
    copy = pathlib.Path(tempfile.mkdtemp(prefix="mutant-"))
    for name in filter(None, names.split("\0")):
        target = copy / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, target, follow_symlinks=False)
    if (root / NODE_MODULES).is_dir():
        (copy / NODE_MODULES).parent.mkdir(parents=True, exist_ok=True)
        os.symlink(root / NODE_MODULES, copy / NODE_MODULES, target_is_directory=True)
    return copy


def _compiles(copy: pathlib.Path, file: str) -> str | None:
    """Why the changed file does not compile, or None."""
    path = copy / file
    text = path.read_text(encoding="utf-8")
    try:
        if file.endswith(".py"):
            compile(text, str(path), "exec")
        elif file.endswith(".json"):
            json.loads(text)
        elif file.endswith((".yml", ".yaml", ".cff")):
            yaml.safe_load(text)
    except (SyntaxError, ValueError, yaml.YAMLError) as exc:
        return f"{file} does not compile: {str(exc).splitlines()[0] if str(exc) else type(exc).__name__}"
    if file.startswith(BUNDLED):
        for command in ([sys.executable, str(copy / BUNDLER)], ["node", "--check", str(copy / BUNDLE)]):
            done = subprocess.run(command, cwd=copy, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            if done.returncode != 0:
                said = (done.stderr or done.stdout).strip().splitlines()
                return f"{file} does not compile: " + (said[-1] if said else " ".join(command[-2:]) + " failed")
    return None


def _verdict(done: subprocess.CompletedProcess) -> tuple[str, str]:
    """(status, why) from pytest's exit code and its last lines."""
    lines = [line for line in (done.stdout + done.stderr).splitlines() if line.strip()]
    tail = "\n".join(lines[-6:])
    if done.returncode == 1:
        return "killed", ""
    if done.returncode == 0:
        if re.search(r"\b\d+ passed\b", tail):
            return "survived", "the test passed on the mutant:\n" + tail
        return "broken", "no test ran (skipped, or nothing collected):\n" + tail
    return "broken", f"pytest exit {done.returncode}:\n" + tail


def run(root: pathlib.Path, listed: list[dict], only: str | None = None, say=print) -> list[Outcome]:
    out = []
    known = controls(root)
    for row in listed:
        if only is not None and row["id"] != only:
            continue
        began = time.perf_counter()
        wrong = faults(row, root, known)
        if wrong:
            outcome = Outcome(row["id"], "broken", time.perf_counter() - began, "; ".join(wrong))
        else:
            copy = _copy(root)
            try:
                path = copy / row["file"]
                if not path.is_file():
                    outcome = Outcome(row["id"], "broken", time.perf_counter() - began, f"{row['file']} is not tracked by git")
                    out.append(outcome)
                    say(f"{outcome.status:<9} {outcome.id:<44} {outcome.seconds:5.1f} s  {row['file']}\n          {outcome.why}")
                    continue
                path.write_text(path.read_text(encoding="utf-8").replace(row["find"], row["replace"], 1), encoding="utf-8")
                try:
                    why = _compiles(copy, row["file"])
                    if why is not None:
                        outcome = Outcome(row["id"], "broken", time.perf_counter() - began, why)
                    else:
                        done = subprocess.run(PYTEST + row["test"], cwd=copy, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
                        status, why = _verdict(done)
                        outcome = Outcome(row["id"], status, time.perf_counter() - began, why)
                except subprocess.TimeoutExpired:
                    outcome = Outcome(row["id"], "broken", time.perf_counter() - began,
                                      f"ran past {TIMEOUT_SECONDS} s and was stopped: a test that does not end shows nothing")
            finally:
                shutil.rmtree(copy, ignore_errors=True)
        out.append(outcome)
        say(f"{outcome.status:<9} {outcome.id:<44} {outcome.seconds:5.1f} s  {row['file']}")
        if outcome.why:
            say("          " + outcome.why.replace("\n", "\n          "))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--only", metavar="ID", help="run this row alone")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT, help="the tree to read (a git working tree)")
    parser.add_argument("--list", type=pathlib.Path, help=f"the mutant list (default: {LIST.as_posix()} under the root)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    listed = rows((args.list or root / LIST).read_text(encoding="utf-8"))
    if args.only is not None and args.only not in {row["id"] for row in listed}:
        print(f"run_mutants: no row is named {args.only}", file=sys.stderr)
        return 2
    began = time.perf_counter()
    outcomes = run(root, listed, args.only)
    counts = {status: sum(1 for o in outcomes if o.status == status) for status in ("killed", "survived", "broken")}
    print(f"{len(outcomes)} mutants: {counts['killed']} killed, {counts['survived']} survived, {counts['broken']} broken"
          f" ({time.perf_counter() - began:.0f} s)")
    return 0 if outcomes and counts["killed"] == len(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
