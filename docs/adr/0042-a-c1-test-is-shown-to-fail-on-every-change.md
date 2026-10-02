# 0042 — A C1 test is shown to fail on every change, by a mutant kept in the repository

- Status: accepted
- Decided: 2026-10-02
- Amends: [0041](0041-a-finding-is-closed-by-a-control.md) (how a C1 test is shown to fail: on every change, not once by hand)

## Where it came from

ADR 0041 makes a test worth what it fails on: a C1 test is "shown to fail — on the code before the
fix, or on a mutant of the code after it". The showing was made once, by hand, when the fix was
made, and the pull request said how. Nothing made it again. The reviews of 0.2.0 had already found
two controls of that kind that had stopped biting — a limit whose only test patched the constant it
claimed to hold, a guard no test reached — and the reviews of 0.3.1 found two more: the checker's
gate claimed a planted violation is found in endnotes and footers, and taking both out of the code
left every test green (`V31-05` in `tests/regressions.yaml`); a timing test held both
implementations to one fixed ceiling, which the slower one passed by reading every run inside each
run again (`V31-12`). Every gate was green while each of them did not hold.

## Decision

**A C1 test is shown to fail on every pull request and at the tag, on a mutant kept in the
repository.** `tools/mutants.yaml` holds the mutants: each row is one change to one tracked file,
written as the text to find — in that file exactly once — and the text to put in its place, the
test that must fail on it, and the ledger row or gate the mutant holds. `tools/run_mutants.py`
copies the tracked files, makes one row's change in the copy, compiles what it changed, runs the
named test there and counts: a kill is pytest's exit 1 and nothing else; a mutant that survives,
a change found nowhere or twice, a change that does not compile, a test that is not there, did
not run or did not end, are each named, and each fails the run. The `tests` job runs it on every pull request,
after the coverage report, and `release-check` runs it at the tag — so a mutant that survives is
seen before a tag, which cannot be moved (`.github/workflows/gates.yml`, `release.yml`;
`tests/test_mutants.py` holds the list to its shape and the runner to its verdicts).

What the list holds, and how it grows:

1. It began with the mutants the reviews of 0.2.0 planted by hand — the limits at their values,
   the checker's causes and refusals, the build's fidelity check and its defaults, the bundle, the
   settings registry, the licence lines, the citation — and one mutant for each ledger row of
   0.3.1, 0.3.2 and 0.3.3 whose test can be turned red by one change.
2. From this record on, **every new ledger row comes with its mutant**: the defect a pull request
   says it planted and saw red is a row of the list, so it is planted and seen red again on every
   change.
3. A limit both implementations state has a mutant on each side — the Python constant and the
   JavaScript one — each killed by the test that reads both.
4. The ledger rows before 0.3.1 that the reviews did not plant by hand have no row yet. Each gets
   one when the code under it is next changed, written by the person changing it; none is written
   by a tool over code nobody read.

Left out on purpose:

- **Generated mutants** — an operator over every constant and branch. A mutant nobody chose names
  no control. Every row is read by a person and says what it holds.
- **A mutation score.** The run passes when every mutant is killed and fails otherwise; a
  percentage would let a surviving mutant through as a number.
- **Three rows of 0.3.1.** `V31-02` and `V31-07` are held by tests of `repair` alone, and no
  mutant is written on `repair`; `V31-12` was a fault in a test's own ceiling, and the test now
  measures a ratio, which no change to the code can show.

## Why

ADR 0041 puts a test above a rule because the suite reads the test on every change. A test shown
red once and never again is read on every change but proven on none, and the two findings of
0.3.1 above are what that costs. A mutant kept beside the code is the showing made repeatable, in
the same place and at the same time as the suite, so the proof is as current as the test. The
limits are the plainest case: the reviews of 0.2.0 raised each one tenfold with every test green,
and the test that now reads each constant from both implementations is itself held by the mutant
that raises one.

## Expires when

A mutant is kept green by changing its row rather than the code, or the list stops growing with
the ledger — then the showing is a form again, and this record is restated with what shows a test
red.
