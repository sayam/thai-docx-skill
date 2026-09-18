# 2026-09-18 — grill read one message two ways; now it reads it one way

Three adversarial reviews were run against v0.1.1 on 2026-09-18 — Codex (GPT-5), Cursor with
Grok 4.6, Cursor with Composer — and every claim was re-run here before it was believed. Two of the
confirmed findings are the same defect seen from two sides: **`grill` did not read the user's
message the way its records say it does.**

## What was wrong

### The two implementations disagreed on the length of a message

ADR 0029 caps the message at "the first 20,000 **characters**". Python counted characters; the
JavaScript counted UTF-16 units, so a character outside the BMP counted twice:

```
$ M=$(python3 -c 'print("😀"*10000+" thai-docx grill")')
$ python3 skills/thai-docx/scripts/thai_docx    grill --said "$M"   → "mode": "grill"
$ node    skills/thai-docx/scripts/thai_docx.js grill --said "$M"   → "mode": "build"
```

10,000 emoji and the phrase is 10,016 characters and 20,016 UTF-16 units. The JavaScript cut the
message at 20,000 units, which fell inside the phrase, and reported build mode. A user who typed
`thai-docx grill` in a message with emoji in it got the interview from one implementation and not
from the other — against ADR 0008, and against the parity test's own words, "both read the message
the same way".

### The phrase would not take a space

ADR 0026 §43–44: the phrase is read "with `-`, `_` or a space between the two words of the name".
`fold` turned `_` into `-` and never touched the space, so of the three spellings the record
promises, one did not work:

```
thai-docx grill → grill      thai_docx grill → grill      Thai-Docx Grill → grill
/thai-docx grill → grill     thai docx grill → build   ← the record says grill
```

The comment three lines above the constant said the space was allowed. The code had never done it,
and no test asked.

## What changed

Both implementations now read the phrase with one pattern, `thai[- ]docx grill`, applied to the
folded message — a space is allowed exactly where the name's two words meet, and nowhere else,
because a space is also what separates the phrase's own words. The pattern's end is where the parts
after it (`from`, `save to`, `only`) start being read, so a message written either way is parsed
from the same place.

The JavaScript now counts the cap in characters: `[...message]` before the length test and before
the slice, so a character outside the BMP is one character and a surrogate pair is never cut in
half.

## Tests, red before the change

- `tests/test_grill.py::test_the_phrase_is_read_with_a_space_between_the_two_words` — the six
  spellings the records allow all give grill mode; `thai.docx grill`, `thaidocx grill`,
  `thai docxgrill` and `docx grill` give build; a tab or a double space still reads as the phrase,
  because `plain` makes every run of whitespace one space; and `parts` reads `from report` from the
  same place whichever way the two words were joined.
- `tests/test_grill.py::test_the_cap_counts_characters_not_units_of_storage` — 10,000 emoji plus
  the phrase is grill mode; 20,000 emoji plus the phrase is build mode.
- `tests/test_js_parity.py::test_command_line_is_the_same` — two rows added: the space spelling, and
  the 10,000-emoji message. This is the row that was red before the fix.

224 tests pass, ruff and ESLint are clean, and `tools/bundle_js.py` regenerated the bundle.

## What it says about the suite

Neither defect is about Thai, and neither needed a subtle reading of OOXML. They needed two inputs
nobody had tried: a character outside the BMP, and the third spelling of a phrase the project's own
comment promised. The suite had 222 tests and neither case.

The other four findings confirmed in the same triage — a truncated PNG accepted as an image, a valid
but oversized image reported through the exit code that means "this skill is broken", `check` never
opening `word/comments.xml`, and records still citing ADR 0025 and 0003 — are recorded in
`.local/work/2026-09-18-review/TRIAGE.md` with their reproductions and are fixed after this one.
