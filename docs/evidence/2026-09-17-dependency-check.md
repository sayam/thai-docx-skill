# 2026-09-17 — the dependency check: red on a known vulnerability, green after the bump, closed on a missing lockfile

What this proves: the `deps` job reads both pinned dependency files, fails on a known
vulnerability in them, passes once it is fixed, and fails — rather than passes — when a file it
names is missing.

Environment: GitHub Actions `ubuntu-latest`; OSV-Scanner 2.6.0 from
`ghcr.io/google/osv-scanner-action@sha256:71ad04ab…c174a`, called as `osv-scanner scan source`
with `--lockfile=requirements.txt:requirements/dev.txt --lockfile=tests/js/package-lock.json`.
Locally the same binary, taken from that image's layer (sha256 `a0496643…3c8e`, checked against
the manifest).

## Red, then green

| commit | `requirements/dev.txt` | `deps` |
|---|---|---|
| f96f2fc, run [35226281263](https://github.com/sayam/thai-docx-skill/actions/runs/35226281263) | pytest 8.4.2 | **failure**: 17 PyPI and 83 npm packages read; PYSEC-2026-1845 / GHSA-6w46-j5rx-g56g, pytest 8.4.2, CVSS 6.8 (medium), fixed in 9.0.3 |
| the bump that follows | pytest 9.1.1 | success: "No issues found" (locally the same) |

The advisory: pytest through 9.0.2 on Unix uses `/tmp/pytest-of-{user}` directories that another
local user can take over. The bump goes to 9.1.1, the latest release (PyPI hash
`37a86b45…4f0c`, the same wheel for every Python); its requirements — pluggy, iniconfig,
packaging, pygments — are met by the versions already pinned. The suite passes on it (217
passed, Python 3.13 locally, 3.11 in CI).

## Closed on a missing file

`--lockfile=requirements.txt:requirements/missing.txt`: "failed to resolve path … no such file or
directory", exit 127. Calling `osv-scanner` directly matters here: the published action's wrapper
script turns exit 128 ("no lockfiles") into 0.

## Not proved here

- A malicious-package finding: none was planted.
- The release workflow's step: it runs the same command, and runs only on a release.
