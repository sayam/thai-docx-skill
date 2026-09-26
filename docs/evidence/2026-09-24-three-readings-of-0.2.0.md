# 2026-09-24 — three readings of 0.2.0, and what became of each finding

What this proves: 0.2.0 was read three ways on the day it was released, every finding was
reproduced before it was believed, and each one v0.2.1 closes is held by a test named in
`tests/regressions.yaml`. What it does not prove: that the readings found everything, or that
anything found only by reading behaves as described in an application — the rows marked
`office-app` or `agent-run` there still owe that reading.

Environment: `main` at `b6dc363` (tag `v0.2.0`), Linux, Python 3.13, Node.js 24, the suite at
351 tests. Every reading was done in a copy; the checkout itself was not touched (its
`git status --porcelain` was empty before and after).

## The three readings

| reading | what it looked at | found |
|---|---|---|
| a review of the code for bugs and vulnerabilities | `repair` and the package; `build`, `profile` and `grill`; `check` and CI | R1–R5, B1–B4, D1–D5, S1–S5, C1–C7, and observations |
| two outside reviews, each finding reproduced here | the same commit | 12 findings, all of which reproduced; 7 not in the first reading: R6, B5–B8, C8 and a stale version string |
| a review to the project's own quality prompt, in six areas — docs, OOXML and Thai, CommonMark and parity, security, the agent's reading of SKILL.md, gates and records | the same commit | 90 findings: severity 1 ×2, 2 ×8, 3 ×28, 4 ×46, design ×6 |

A finding was believed only when it reproduced here, in both implementations where both apply,
with its input kept. A finding that needed a real application to confirm was marked so, and
was not counted as confirmed.

## What became of them

**Closed in v0.2.1**, each by a test that fails without the fix — the row, its class and its
test are in `tests/regressions.yaml`, which `tests/test_regressions.py` holds to naming a test
there is:

| pull request | what it closed |
|---|---|
| #85 | what every command reads, writes and accepts: R3, R6, D4, D-05, D-04, B2, C-05, D-02, E-04, B4, B6, B3, D-07, D-13, B1, E-15, C-03, D-15, D3 |
| #86 | repair's reading of XML: R1, R2, R4, R5, D2, B-01, B-02, A-01, D-06, D-08, D-10, B-12, F-01 |
| #87 | the checker and its limits: D-01, D-03, F-02, D-09 — and one found while writing D-09's test: a chain of 41 symbolic links embedded a picture from outside the Markdown's directory (D-09a) |
| #88 | the build, the parser and grill: B5, B-06, B8, B-07, D1, C-02, B-03, C-11, C-04, C-06, C-07, D5, B7, E-08, E-16, and the stale version string |
| #89 | the release and CI: S1, S2, F-03, F-05, F-09, F-10, F-11, A-04 |
| #90, #91 | a profile that hides another (A-03, E-02); the docs (E-01, E-03, E-05–E-07, E-09–E-14, E-18–E-20, A-06, A-08–A-10); `--allow-dir` of the root (D-16) |
| this record's pull request | the records: A-02, F-04, F-06, F-12, F-13 |

**Decided, not fixed, in v0.2.1**, and why:

- **C-01** — emphasis and link labels read the runtime's Unicode tables, so Python and Node on
  different Unicode versions can read one character differently. Recorded as a limit
  (`references/limits.md` §11), and ADR 0008 is amended by ADR 0040: the same bytes on the same
  Unicode version. Shipping the tables with the skill is weighed for 0.3.
- **B-05** — `พ.ศ.` is cut into several runs at its full stops. Whether Word draws it wrongly is
  read with the five applications after v0.2.1 is tagged; any change moves bytes, so it is 0.3's.
- **E-21** — the skill's description. What triggers a skill is measured in the model-equivalence
  runs, not argued; it waits for them.
- **F-14** — where the two thesis pictures came from is not written down; the maintainer states it.

**Deferred to 0.3**, because each moves the build's bytes or widens what the checker judges, and
v0.2.1 moves no golden: C1–C8 and B-04 (the checker's reach), S3–S5 (the release workflow's
remaining hardening), B-09, B-10, B-13 (complex script outside the Thai block, normalisation,
accessibility of tables and pictures), C-09, C-10, C-13 (dialect against cmark-gfm), E-17, E-24,
D-11, D-12, D-14, and ADR 0037's renumbering.

## The rule that came of it

Two of the findings — a limit held by a test that patched the constant it claimed to hold, and a
guard no test ever reached — had been written down as lessons before. A lesson in prose had come
back. ADR 0041 records what closes a finding from now on.
