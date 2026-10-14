# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Every workflow runs with the least privilege and within a bound (gate workflows-are-least-privilege-and-bounded).

Planted on 2026-10-14: `permissions: contents: read` taken off `gates.yml`, and every
`timeout-minutes` taken out of it, left the doctor and the suite green — two rules held by words
(V35-08). This holds every workflow under `.github/workflows` to: `contents: read` and nothing more
at the top; a `timeout-minutes` of 1 to 60 on every job; a job's own permissions, where it needs
more, as named scopes and never `write-all`; `persist-credentials: false` on every checkout, so no
later step finds a token in `.git/config`; and `pull_request`, never `pull_request_target`.
"""

from __future__ import annotations

import copy
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
SCOPES = ("read", "write", "none")


def faults(flow: dict) -> list[str]:
    """What is wrong with one workflow, read as YAML — a line commented out is not a line."""
    out = []
    if flow.get("permissions") != {"contents": "read"}:
        out.append("the workflow grants more than contents: read at the top")
    events = flow.get("on", flow.get(True, {}))  # PyYAML reads a bare `on` as the boolean True
    if "pull_request_target" in (events if isinstance(events, (dict, list)) else [events]):
        out.append("the workflow runs on pull_request_target, with a token that can write and the secrets")
    jobs = flow.get("jobs") or {}
    if not jobs:
        out.append("the workflow has no jobs")
    for name, job in jobs.items():
        bound = job.get("timeout-minutes")
        if isinstance(bound, bool) or not isinstance(bound, int) or not 1 <= bound <= 60:
            out.append(f"job {name} has no timeout-minutes between 1 and 60")
        scopes = job.get("permissions", {})
        if not isinstance(scopes, dict) or any(value not in SCOPES for value in scopes.values()):
            out.append(f"job {name} grants permissions that are not named scopes")
        for step in job.get("steps") or []:
            if str(step.get("uses", "")).startswith("actions/checkout@") and (step.get("with") or {}).get("persist-credentials") is not False:
                out.append(f"job {name} checks out and keeps the token")
    return out


def test_every_workflow_runs_with_least_privilege_and_a_bound():
    assert len(WORKFLOWS) >= 5, WORKFLOWS
    for path in WORKFLOWS:
        assert faults(yaml.safe_load(path.read_text(encoding="utf-8"))) == [], path.name


def _planted(change) -> list[str]:
    flow = copy.deepcopy(yaml.safe_load((ROOT / ".github" / "workflows" / "gates.yml").read_text(encoding="utf-8")))
    change(flow)
    return faults(flow)


def _drop_permissions(flow):
    del flow["permissions"]


def _write_all(flow):
    flow["permissions"] = "write-all"


def _widen(flow):
    flow["permissions"]["pull-requests"] = "write"


def _no_bound(flow):
    del flow["jobs"]["tests"]["timeout-minutes"]


def _zero_bound(flow):
    flow["jobs"]["tests"]["timeout-minutes"] = 0


def _long_bound(flow):
    flow["jobs"]["tests"]["timeout-minutes"] = 360


def _job_write_all(flow):
    flow["jobs"]["scans"]["permissions"] = "write-all"


def _keep_token(flow):
    flow["jobs"]["scans"]["steps"][0]["with"]["persist-credentials"] = True


def _no_with(flow):
    del flow["jobs"]["scans"]["steps"][0]["with"]


def _target(flow):
    flow[True]["pull_request_target"] = None


def _no_jobs(flow):
    flow["jobs"] = {}


@pytest.mark.parametrize("change, said", [
    (_drop_permissions, "more than contents: read"),
    (_write_all, "more than contents: read"),
    (_widen, "more than contents: read"),
    (_no_bound, "job tests has no timeout-minutes"),
    (_zero_bound, "job tests has no timeout-minutes"),
    (_long_bound, "job tests has no timeout-minutes"),
    (_job_write_all, "job scans grants permissions that are not named scopes"),
    (_keep_token, "job scans checks out and keeps the token"),
    (_no_with, "job scans checks out and keeps the token"),
    (_target, "pull_request_target"),
    (_no_jobs, "no jobs"),
])
def test_each_fault_is_found_on_a_planted_workflow(change, said):
    found = _planted(change)
    assert len(found) == 1 and said in found[0], found
    assert _planted(lambda flow: None) == []
