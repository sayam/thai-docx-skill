# 2026-09-18 — repair: the compatibility mode, and proofing switched off

The first two repairs of v0.2, on the packer that was finished the same day
([record](2026-09-18-a-package-comes-back-as-it-went-in.md)). [ADR 0032](../adr/0032-repair-rewrites-attributes-never-the-text.md)
lists five findings a repair may touch; this is two of them.

```
thai_docx repair IN.docx OUT.docx
```

| code | what it does |
|---|---|
| `1` | declares compatibility mode 15 — sets the one that is there, drops a second |
| `3` | removes `<w:noProof/>`, wherever in the package it is |

Everything else is reported in `remaining` and left alone.

## On a file another program wrote

`tests/fixtures/legacy-python-docx-default.docx`, which python-docx wrote:

```
$ thai_docx check legacy.docx
findings: 1 × code 1, 4 × code 2, 7 × code 5

$ thai_docx repair legacy.docx fixed.docx
{"ok": true, "repaired": {"1": 1}, "remaining": [… 2 and 5 …], "bytes": 38386}
exit 1

$ thai_docx check fixed.docx
findings: 4 × code 2, 7 × code 5
```

Code 1 is gone; the eleven findings this version does not repair are still there and still
reported. The file grew by 1,576 bytes — the settings part, rewritten and stored, against its
deflated original — and **every other entry kept its own compressed bytes**, which the tests
check entry by entry rather than by comparing content.

The exit code says which of the three happened: **0** repaired and nothing left that this
version repairs, **1** repaired and findings remain, **2** nothing written.

## Why the parts are edited as bytes and not as a tree

Both elements are empty ones — `<w:noProof/>` and `<w:compatSetting …/>` — so their shapes are
few and a targeted edit is exact. Re-serialising a parsed tree would rewrite namespace
prefixes, attribute order and empty-element spelling across the whole part, and ADR 0032
allows only the attributes it names to change. A repair that reformats a part it was asked to
touch has changed more than it said.

`<w:noProof w:val="false"/>` is removed as well as `<w:noProof/>`. Both leave the default,
which is proofing on, so removing either is the same thing said two ways.

## What holds it

`tests/test_repair.py`, gate `repair-changes-only-what-it-names`, fifteen tests:

- each repair on a planted fixture, and both at once;
- **the text comes through character for character** — the comparison ADR 0023 requires,
  between the input's paragraphs and the output's;
- **every part it did not write keeps its bytes**, raw and still compressed, with its method
  and checksum;
- a file whose only findings are ones this version does not repair: **nothing is written**, and
  the findings come back in `remaining`;
- a clean file: nothing written;
- **idempotent** — repairing a repaired file finds nothing to do;
- a missing file, a file that is not a zip, and a package with a DOCTYPE are refused exactly as
  `check` refuses them, and nothing is written;
- the three exit codes;
- the file opens in Python's `zipfile` and passes `testzip()`.

`tests/test_js_parity.py` runs six `repair` command lines through both implementations — a
file to repair, a clean file, a file that is not a zip, a missing file, one path instead of
two, and an output path that cannot be written. **The bytes and the JSON match.** The repaired
`legacy.docx` is the same sha256 from Python and from Node.

263 tests pass.

## What is not repaired yet, and why it matters to say

Codes `2` and `5` — the marks a Thai run needs, and the complex-script twins — are the common
findings, by a distance: eleven of the twelve in the file above. A user who repairs a file
today gets a document that is still wrong for Thai, and the report says so. Every page that
mentions repair says so too: `references/repair.md`, `references/check.md`, both command-line
guides and both scenario pages. Claiming a fix that has not happened would be worse than not
fixing it.

Those two need a decision this version does not have to make: which complex-script font to
give a run that has none. ADR 0032 says the repair reports the choice; the record for it comes
with the code.
