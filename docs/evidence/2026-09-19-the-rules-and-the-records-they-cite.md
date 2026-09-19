# 2026-09-19 — the rules, and the records the project cites

What this proves: the gate `live-pages-cite-the-record-in-force` (`tests/test_rules.py`) is red on
a rules page whose trace cannot be followed, and on a live page that sends a reader to a record the
index marks superseded.

The check is the one `ROADMAP.md` had been carrying since 2026-09-18 as worth having and not built:
the citation drift of that day was found by a reviewer, not by a gate. It is built now because
`docs/rules.md` states, in the rules themselves, that only a record still in force may be cited —
a claim that has to be held to something.

## What the scan found on the day it was written

Twenty-three files, `main` at 4f141a1, were pointing at records the index had marked superseded —
0005 (restated by 0016, then 0023), 0010 (0022), 0011 (0025, then 0030), 0025 (0030) and
0026 (0029). Three of them were **messages a user reads**, not comments:

```
skills/thai-docx/scripts/thai_docx/markdown.py:1785
    text contains {label}; the build refuses it (ADR 0005, 0015)
skills/thai-docx/scripts/thai_docx/markdown.py:1801
    footnote [^{label}] is defined but never referenced; nothing may be dropped silently (ADR 0005)
js/40-markdown.js:1694, 1709 — the same two, in the other implementation
```

The numbering was mapped, not substituted, as `2026-09-18-records-point-at-the-record-in-force.md`
says it must be:

```
ADR 0005 §1, §2, §4 → ADR 0023 §1, §2, §4   (0023 restates them in order and adds §5, captions)
ADR 0011 §7         → ADR 0030 §9           (DOCTYPE, package size)
ADR 0025 §N         → ADR 0030 §N
ADR 0026            → ADR 0029
```

`.github/SECURITY.md` was among them ("what the scripts are designed never to do is written down in
`docs/adr/0025`"), and so was one gate's own title in `gates.yaml`.

## The defects planted, and what each did

Each was planted alone, `python3 -m pytest -q tests/test_rules.py` run, then reverted.

| planted | result |
|---|---|
| — (the tree as it stands) | `6 passed` |
| `GOVERNANCE.md` cites ADR 0011 instead of 0018 | `1 failed, 5 passed` |
| a source comment goes back to `(ADR 0026)` alone | `1 failed, 5 passed` |
| the same line says `(ADR 0026, restated by 0029)` | `6 passed` — history, said as history |
| a trace link points at a file that is not there | `2 failed, 4 passed` |
| the trace cites 0016, which 0023 replaced | `2 failed, 4 passed` |
| `docs/architecture.md` stops linking the rules | `1 failed, 5 passed` |
| `# Reference translation` renamed `# Translation` | `3 failed, 3 passed` |

The failing test names which page and line in each case, as
`GOVERNANCE.md:31: ADR 0011 superseded by 0025`.

## What the gate does not read, and why

`docs/adr/`, `docs/evidence/`, `docs/handoff/` and `CHANGELOG.md` record what was true on a day: a
record cites what was in force when it was written, and rewriting them would make the history say
something nobody observed. `tools/` is verifiable-gates, installed and hash-checked, with a
numbering of its own — `tools/overlay.json` cites an "ADR 0062" that belongs to another project.

That line — a page that **states a rule now** points at the record in force, a page that **records
what happened then** keeps the name it was written with — is the one drawn on 2026-09-18, and this
gate is its first automatic reader.

## Alongside

312 tests pass, the gates doctor is clean, ruff and ESLint are clean, and the bundle was rebuilt so
the shipped JavaScript carries the corrected citations too. No document bytes changed: the goldens
are untouched, so this needs no new check in the five office applications.
