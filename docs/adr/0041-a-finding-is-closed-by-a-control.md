# 0041 — A finding is closed by a control, not by a fix

- Status: accepted
- Decided: 2026-09-26

## Where it came from

The readings of 0.2.0 on 2026-09-24 ([record](../evidence/2026-09-24-three-readings-of-0.2.0.md))
found two faults the project had already written down as lessons. A limit was held by a test that
patched the constant it claimed to hold; a guard that refuses a repair which changes the text had
never been reached by any test, so switching it off left the suite green. Both lessons were prose,
read by whoever happened to read them. The change that fixed each fault had been announced in
the changelog, under `Fixed`, citing no test at all: fifteen such lines in 0.2.0, none naming one.

A fix says a fault is gone today. Nothing in it says the fault stays gone.

## Decision

**A finding is closed by the control that holds it closed**, and every finding closed from 0.2.1
on is a row of `tests/regressions.yaml`: its name, the fault as a user or an agent met it, its
class, what found it, and the test that fails if it returns.

The classes, from strongest to weakest:

| class | what holds the fault closed | read by |
|---|---|---|
| **C0** | the wrong path no longer exists — one reader with a ceiling, one escape point, one list both implementations read | the code's shape, and a test of it |
| **C1** | a test that fails when the fault returns, shown to fail — on the code before the fix, or on a mutant of the code after it | the suite, on every change |
| **C2** | a rule a person or a model reads — SKILL.md, a reference, CONTRIBUTING | whoever reads it, sometimes |
| **C3** | a check after the work, by a person or in a real application — the five applications, the model-equivalence runs | a record, dated |

The rule:

1. Every row carries C0 or C1. A finding with neither is not closed.
2. **C2 only beside C1.** A rule only a model reads is a rate; a rule a script reads is a verdict. A
   sentence in SKILL.md that closes a finding is held by a test that the sentence is there, and
   whether a model obeys it is measured, not assumed.
3. **C3 only with its record.** A row that rests on a reading names the record it is written in.
4. From the release after 0.2.0, **every line under `### Fixed` in the changelog names the test**
   that fails without the fix, as `tests/<file>.py::<test>`.
5. What found a finding is kept with it — a review, an outside review, a parity run, a planted
   input, an agent's run, an office application — so that when that part of the code changes, the
   activity that found the fault there is the one run again.

`tests/test_regressions.py` holds every row and the changelog to this. It is a test of the project
rather than a rule of the gates doctor because the doctor is installed from verifiable-gates and
pinned by hash, and is not changed here.

Left out on purpose: a class for "fixed and watched" — watching is C3 and needs its record — and
any exception for small findings. A finding too small to hold is too small to announce as fixed.

## Why

A lesson written as prose had come back under a lesson that said so, and a limit whose only test
patched its constant could be raised tenfold with everything green. The hierarchy of controls —
remove the hazard, then guard it, then warn of it, then inspect for it — is the order the classes
take, and the order a finding should be closed in when there is a choice. A test is worth what it
fails on, so a C1 test is shown failing before it is trusted to pass.

## Expires when

The project stops announcing fixes, or a finding arises that no test and no dated reading can hold
— then this record is restated with what closes that one.
