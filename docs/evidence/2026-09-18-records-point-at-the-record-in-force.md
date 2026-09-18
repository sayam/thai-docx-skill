# 2026-09-18 — the live pages point at the record in force

The fourth item of the triage from the adversarial reviews of 2026-09-18. Cursor's Grok 4.6 read the
ADR index, saw that 0025 and 0003 were superseded on 2026-09-18 by 0030 and 0031, and then found
both still cited across the project as if they held.

This is drift the project caused itself, in the same day's work, and it is the kind a reader meets
first: the assurance case names the record its requirements come from, and that name was a record
whose own status line says "superseded".

## What was pointing where

| page | said | now says |
|---|---|---|
| `docs/assurance-case.md` | ADR 0025 §1–§9, with a link to 0025 | ADR 0030, same section numbers |
| `docs/architecture.md` | "limits: ADR 0025", and 0025 in the properties table | ADR 0030 |
| `.github/CONTRIBUTING.md` | "The limits of ADR 0025" | ADR 0030 |
| `ROADMAP.md` | "no network… (ADR 0025)" | ADR 0030 |
| `gates.yaml` | `javascript-matches-python` cited ADR 0011; `python-stays-within-the-script-limits` cited 0025; `sources-name-their-licence` cited 0003 | 0030, 0030, 0031 |
| the skill's Python and JavaScript | 0011 and 0025 in module headers, in the profile size cap, and in **the message a user reads** when an image lies outside the Markdown's tree | 0030 |
| the tests | 0025 and 0003 in the docstrings that say what each file holds | 0030, 0031 |

## The numbering had to be mapped, not substituted

0011's limits were renumbered when 0025 restated them: 0011 grew two sections, so the rule about
DOCTYPE and package size moved from §7 to §9, and the one about logs and text from §6 to §8. A
find-and-replace of "0011" for "0030" would have left every section number one or two out — a
citation that looks right and sends the reader to the wrong rule. The map used:

```
ADR 0011 §4 → ADR 0030 §4    (images)
ADR 0011 §6 → ADR 0030 §8    (logs carry no document text)
ADR 0011 §7 → ADR 0030 §9    (DOCTYPE, package size)
ADR 0025 §N → ADR 0030 §N    (0030 restates 0025 with the same numbering)
```

## What was deliberately left alone

**Evidence records and the changelog.** `docs/evidence/2026-09-15-…` through `…-09-17-…` cite 0011
and 0025 because those were the records in force on the day each was written, and the changelog
entry for 0.1.0 says the limits were "restated for it (ADR 0025, superseding 0011)", which was true
of that release. A record of what was seen on a date is not corrected later; it is superseded, and
the index says so. Rewriting them would make the history say something nobody observed.

The line between the two: **a page that states a rule now** points at the record in force; **a page
that records what happened then** keeps the name it was written with.

## How it will not happen again

The ADR index (`docs/adr/README.md`) is held by `tools/gates_doctor.py` against the files beside it,
so a superseded record cannot vanish or lose its row. Nothing holds the *citations* — and after
today, three of the four review findings in this batch were defects while this one was drift, which
is a fair share for a project that supersedes records as often as this one does. A check that reads
every live page for a citation of a superseded record is worth having; it is written down in
`ROADMAP.md` rather than built today, because the fix above is what the reviewer actually found.

227 tests pass, the gates doctor is clean, ruff and ESLint are clean, and the bundle was regenerated
so the shipped JavaScript carries the corrected citations too.
