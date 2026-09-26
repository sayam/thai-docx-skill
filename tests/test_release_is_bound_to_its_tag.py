# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A release is built from its tag and proven to be, and every page says how to check it the
same way (ADR 0012, 0018).

The review of 0.2.0 found three gaps a workflow run could not show. `actions/checkout` given a
bare tag name looks among the branches first, so a branch named like the tag would be built in
its place. The attestation was verified against the repository only, so one another workflow or
another ref made for the same bytes would pass — and the install guides' command did not even
name the workflow. And the tag was held to the suite but not to the lints or the coverage floor
the gate claiming it names. None of this runs until a tag is pushed, so it is read here.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RELEASE = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
GATES = (ROOT / ".github" / "workflows" / "gates.yml").read_text(encoding="utf-8")
PAGES = ["README.md", ".github/SECURITY.md", "docs/guide/en/install.md", "docs/guide/th/install.md",
         ".github/workflows/release.yml"]
WORKFLOW = "sayam/thai-docx-skill/.github/workflows/release.yml"


def commands(text: str) -> list[str]:
    """Each `gh attestation verify` command, its continued lines joined, comment marks and
    backquotes and double quotes taken off."""
    joined = re.sub(r"\\\n\s*#?\s*", " ", text).replace("`", " ").replace('"', "")
    joined = re.sub(r"\n\s*(?=--)", " ", joined)  # a Markdown line that goes on with a flag
    return [m.group(0) for m in re.finditer(r"gh attestation verify [^\n]*", joined)]


def test_every_way_to_verify_a_release_names_the_workflow_and_the_tag():
    found = 0
    for page in PAGES:
        for command in commands((ROOT / page).read_text(encoding="utf-8")):
            if "tampered" in command or not re.search(r"\.zip|\$ZIP", command):
                continue  # the workflow's own proof that a changed file fails, or prose naming the command
            found += 1
            workflow = "$GITHUB_REPOSITORY/.github/workflows/release.yml" if "$GITHUB_REPOSITORY" in command else WORKFLOW
            assert "--signer-workflow " + workflow in command, (page, command)
            ref = re.search(r"--source-ref (\S+)", command)
            assert ref is not None, (page, command)
            version = re.search(r"thai-docx-([^ ]+?)\.zip", command)
            if version is not None:  # a page names the archive; the ref names the same release
                assert ref.group(1) == "refs/tags/v" + version.group(1), (page, command)
    assert found >= 8, found


def test_the_release_checks_out_the_tag_as_a_tag_and_proves_it():
    refs = re.findall(r"^\s+ref: (.*)$", RELEASE, re.M)
    assert refs and all(r.startswith("refs/tags/") for r in refs), refs
    assert RELEASE.count('test "$(git rev-parse HEAD)" = "$(git rev-parse "refs/tags/$TAG^{commit}")"') == len(refs)
    assert '[[ "$TAG" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+$ ]]' in RELEASE  # a dispatch names a release tag or nothing


def test_the_tag_passes_the_gates_a_pull_request_passes():
    check = RELEASE[RELEASE.index("  release-check:"):RELEASE.index("  release-archive:")]
    for step in ("python3 tools/gates_doctor.py", "ruff check --no-cache skills/thai-docx/scripts tools tests",
                 "eslint --config tests/js/eslint.config.cjs js", "python3 -m coverage run -m pytest -q tests",
                 "python3 -m coverage report", "osv-scanner"):
        assert step in check, step


def test_the_suite_runs_on_the_oldest_and_the_newest_runtimes_promised():
    newest = GATES[GATES.index("  tests-newest:"):]
    newest = newest[:newest.index("\n  # ")]
    assert 'python-version: "3.13"' in newest and 'node-version: "24"' in newest and "pytest -q tests" in newest
    oldest = GATES[GATES.index("  tests:"):GATES.index("  tests-newest:")]
    assert 'python-version: "3.11"' in oldest and 'node-version: "22"' in oldest


def test_what_the_tools_import_the_requirements_pin():
    """tools/preflight.py reads YAML and nothing installed it: `import yaml` stopped it in the very
    environment CONTRIBUTING has a contributor build."""
    pinned = {m.group(1).lower() for m in re.finditer(r"^([A-Za-z0-9_.-]+)==", (ROOT / "requirements" / "dev.txt").read_text(encoding="utf-8"), re.M)}
    provides = {"yaml": "pyyaml", "strictyaml": "strictyaml"}
    for tool in sorted((ROOT / "tools").glob("*.py")):
        for name in re.findall(r"^\s*import (\w+)|^\s*from (\w+) import", tool.read_text(encoding="utf-8"), re.M):
            module = name[0] or name[1]
            if module in provides:
                assert provides[module] in pinned, (tool.name, module)
