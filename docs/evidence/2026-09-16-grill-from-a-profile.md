# 2026-09-16 — grill from a profile, save as another: 13 planted defects, and a path both runtimes now write alike

What this proves: the grill command of ADR 0029 reads `from`, `save to` and `only` (and
`จาก`, `บันทึกเป็น`, `เฉพาะ`) from the user's message, marks the choice each setting holds
in the start profile, gives the args that make each choice true against it — including
`--default` for an answer that undoes a profile's "yes" — and that `--default` does so on
`build --profile` and `profile save --from`; that both implementations answer alike; and
that each of these is held by a test that fails when it is broken.

Environment: Linux, Python 3.13.3, pytest 8.4.2, Node.js 24.15. Content synthetic.

## 1. The flow, end to end

`tests/test_grill.py::test_the_answers_run_as_next_says_give_the_settings_chosen`: a profile
`thesis` (Angsana New, 15 pt, Thai distributed, 1 in margins, a table of contents); the
message `thai-docx grill from thesis save to thesis-v1`; the answers 2b (14 pt) and 6a (no
table of contents). The args the command gives for those two choices, run as its `next`
says (`profile save thesis-v1 --from thesis --size 14 --default toc`), write exactly
`{font, size 14, align, margins}`; a build with `--profile thesis-v1` has the same sha256 as
the build with those settings typed as flags, and so does `--profile thesis` with the same
args and no save.

## 2. A parity fault found on the way

Python reports a profile given by path as `pathlib` writes it (`./a//b.json` → `a/b.json`);
the JavaScript reported it as typed. The fault was in v0.1's `profile show` and `export`
too: every parity case named a path already in its normal form (the shape of L-0010). The
JavaScript now writes the path as Python does on POSIX, and the command-line parity cases
name `./.thai-docx//profiles/./report.json` for `profile show` and for `grill … from`.

## 3. Planted defects

Harness as in `2026-09-16-adr-0027-mutations.md`: one exact text replaced, the bundle
rebuilt, the whole suite run, every red test listed, the file restored and every hash
checked; a control run at the end.

| # | planted defect | red | named by |
|---|---|---|---|
| 0 | Python: a "no" against a profile's "yes" gives no `--default` | 3 | start profile marks what holds; the answers run as `next` says; parity |
| 1 | Python: a choice that already holds still carries args | 3 | start profile …; the command says the mode; parity |
| 2 | Python: the save question asked though the message named the name | 2 | start profile …; parity |
| 3 | Python: an "other" value the list lacks is not marked current | 1 | start profile … |
| 4 | Python: a Thai word written against its value is not read | 2 | the words after the phrase; parity |
| 5 | Python: `save to` takes a path | 2 | the words after the phrase; parity |
| 6 | Python: a part given twice keeps the last | 2 | the words after the phrase; parity |
| 7 | Python: `False` and `0` read as the same setting value | **0** | — |
| 8 | Python: `build --profile` ignores `--default` | 3 | `--default` takes settings out; the answers run …; parity |
| 9 | Python: `--default` takes any word | 2 | `--default` takes settings out; parity |
| 10 | JS: a "no" against a profile's "yes" gives no `--default` | 1 | parity (command line) |
| 11 | JS: a profile path reported as typed | 1 | parity (command line) |
| 12 | JS: `build --profile` ignores `--default` | 1 | parity (command line) |

12 red, one green; control run green (209 passed), every hash back.

**#7 is a redundant guard, not a missing test** (L-0003). The comparison is always between
two values of one setting, and no setting mixes booleans with numbers: `toc` and the other
switches are booleans on both sides, and `page_numbers` is `False` or a position. With the
boolean rule gone, `False` against `False` still compares equal as numbers, and `False`
against `"top-right"` still differs. The rule was removed from both implementations; the
suite stays green (209 passed).

## Not proved here

- That agents ask the questions from the JSON, run what `next` says, and pass the user's
  message whole — the agent runs of the same day,
  `docs/evidence/2026-09-16-agents-after-the-redesign.md`.
- Windows: the JavaScript leaves a path as given there; Python's `pathlib` would rewrite
  back-slashes. No Windows run.

Harness, planted texts and logs: `.local/work/2026-09-16-redesign/mutations-grill/`.
