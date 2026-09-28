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


def release_faults(text: str) -> list[str]:
    """What would let a release go out that its gates never held, read from the workflow as YAML
    — a step commented out, or run only on a condition, is not a step (the review of 0.3.0, F-01:
    eight mutations of release.yml passed a test that looked for substrings)."""
    import yaml
    flow = yaml.safe_load(text)
    out = []
    if flow.get("permissions") != {"contents": "read"}:
        out.append("the workflow's own permissions are more than contents: read")
    jobs = flow.get("jobs", {})
    if jobs.get("release-archive", {}).get("needs") != "release-check":
        out.append("the archive does not wait for release-check")

    def steps(job: str) -> list[dict]:
        return [s for s in jobs.get(job, {}).get("steps", []) if "if" not in s]

    def said(step: dict) -> str:
        return str(step.get("run", "")) + " " + str(step.get("uses", ""))

    check = " ".join(said(s) for s in steps("release-check"))
    # every command a pull request's gates run, but the commit lint (a pull request's range of
    # commits, which a tag has not) and the newest runtimes (run on every push to main)
    gates = yaml.safe_load(GATES)["jobs"]
    for name, job in gates.items():
        if name in ("commits", "tests-newest"):
            continue
        for step in job.get("steps", []):
            command = said(step).strip()
            if command and not str(step.get("uses", "")).startswith(("actions/", "docker://")) and command not in check:
                out.append("release-check does not run: " + command)
    if "osv-scanner" not in check:
        out.append("release-check does not run the OSV scanner")
    if '[ "$GITHUB_REF" = "refs/tags/$TAG" ]' not in check:
        out.append("release-check does not hold the run to the tag it builds")
    archive = [said(s) for s in steps("release-archive")]
    at = {key: next((i for i, s in enumerate(archive) if key in s), None)
          for key in ("package_skill.py --tag", 'package_skill.py "dist/', "gh attestation verify tampered.zip", "gh release upload")}
    if None in at.values():
        out.append("release-archive is missing: " + ", ".join(k for k, v in at.items() if v is None))
    elif not at["package_skill.py --tag"] < at['package_skill.py "dist/'] < at["gh release upload"]:
        out.append("release-archive packs before it checks the versions, or attaches before it packs")
    tamper = archive[at["gh attestation verify tampered.zip"]] if at["gh attestation verify tampered.zip"] is not None else ""
    if len(re.findall(r"if gh attestation verify tampered\.zip[^\n]*; then\n[^\n]*; exit 1\n", tamper + "\n")) < 2:
        out.append("a tampered archive that verifies does not stop the release")
    return out


def test_the_tag_passes_the_gates_a_pull_request_passes():
    assert release_faults(RELEASE) == []


def test_a_release_that_skips_its_gates_is_named():
    """The mutations of F-01, each one caught."""
    mutations = {
        "    needs: release-check\n": "",
        '        run: python3 tools/package_skill.py --tag "$TAG"\n': '        run: "true"\n',
        "permissions:\n  contents: read\n": "permissions:\n  contents: write\n",
        '            echo "a tampered archive verified — the verifier reads nothing"; exit 1': '            echo "x"; exit 0',
        "      - run: python3 -m coverage run -m pytest -q tests\n": "      # - run: python3 -m coverage run -m pytest -q tests\n",
        '      - name: the run is on the tag it builds\n': '      - name: the run is on the tag it builds\n        if: false\n',
    }
    for old, new in mutations.items():
        assert old in RELEASE, old
        assert release_faults(RELEASE.replace(old, new, 1)) != [], old


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


def test_no_checkout_leaves_its_token_behind():
    """S3: `actions/checkout` writes the job's token into `.git/config` unless told not to, where
    every later step — a test, a tool, a script from the tree — can read it. No job here pushes
    with git, so none keeps it."""
    import yaml
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for name, job in yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"].items():
            for step in job.get("steps", []):
                if str(step.get("uses", "")).startswith("actions/checkout@"):
                    assert (step.get("with") or {}).get("persist-credentials") is False, (path.name, name)


def test_a_release_never_replaces_an_asset_it_already_has():
    """S4: `gh release upload --clobber` let a second run put other bytes under a published
    release's name. Without it, an asset already there stops the upload."""
    assert "--clobber" not in RELEASE
    assert re.search(r"gh release upload \"\$TAG\" dist/\*\.zip dist/\*\.intoto\.jsonl\s*$", RELEASE, re.M)


def test_the_readme_says_when_scorecard_reads_a_release():
    """F-15 (the review of 0.2.0): Scorecard read v0.2.0 before its signed archive was attached,
    and the badge fell. It runs on a push to main and weekly, never on a release, and the README
    says so; a trigger added or taken away makes that sentence wrong."""
    import yaml
    flow = yaml.safe_load((ROOT / ".github" / "workflows" / "scorecard.yml").read_text(encoding="utf-8"))
    triggers = flow.get("on", flow.get(True))  # YAML 1.1 reads a bare `on` as true
    assert set(triggers) == {"push", "schedule"}, triggers
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    assert "read on each push to `main` and weekly, not when a release is published" in readme
