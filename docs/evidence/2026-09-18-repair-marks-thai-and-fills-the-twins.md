# 2026-09-18 — repair marks the Thai, and what that costs in bytes

Findings `2` and `5` join `1` and `3`, so `repair` now clears four of the seven codes — including
the two that are almost every broken file's actual problem. It also makes a cost visible that the
plan had not measured.

## What it does

| code | what it writes |
|---|---|
| `2` | `<w:cs/>` and `<w:lang w:bidi="th-TH"/>` on every run that has text |
| `5` | the missing twin of `w:sz`, `w:b`, `w:i`; a `w:cs` font on an `w:rFonts` that names only a Latin one; a Thai-capable font for a Symbol bullet |

On `tests/fixtures/legacy-python-docx-default.docx`, which python-docx wrote:

```
$ thai_docx check legacy.docx
1 × code 1, 4 × code 2, 7 × code 5

$ thai_docx repair legacy.docx fixed.docx
{"ok": true, "repaired": {"1": 1, "2": 8, "5": 7}, "remaining": [],
 "warnings": [{"code": "font", "message": "complex-script font written where a run named none:
               'TH Sarabun New' — this skill's default, as the document names none"}]}
exit 0

$ thai_docx check fixed.docx
{"ok": true, "findings": [], "warnings": []}
```

The text is identical, paragraph for paragraph. Python and Node.js write the same bytes.

Eight code-2 repairs for four findings: the checker reports one finding per run, and a run needs
both the `<w:cs/>` and the language mark, which are counted separately here.

## Elements are inserted where the schema puts them

An `rPr`'s children have a fixed order, and the checker reports `order` when they are out of it. A
repair that appended its additions would trade one finding for another. Each new element is placed
before the first existing child that outranks it, in the order table `check.py` already holds:

```xml
<w:rPr><w:rFonts w:ascii="Angsana New"/><w:b/><w:i/><w:sz w:val="32"/></w:rPr>
→
<w:rPr><w:rFonts w:ascii="Angsana New" w:cs="TH SarabunPSK"/><w:b/><w:bCs/><w:i/><w:iCs/>
       <w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/><w:lang w:bidi="th-TH"/></w:rPr>
```

Nothing already there moves: repairing the order is a different finding, and this version does not
make it.

## The font, and one rule the plan did not have

ADR 0032's order is: `--font` if given, else the complex-script font the document already uses most,
else this skill's default. The middle step needed a rule the plan had not thought of.

The first run of the Symbol-bullet test picked **Symbol** as the document's complex-script font —
it was the most common `w:cs` value in the package, because the broken bullet had put it there. The
repair then "fixed" the bullet by writing Symbol again, and the checker still refused the result.

So: only a font the checker itself accepts is eligible. Writing one it warns about would trade a
finding for a warning, which is not a repair. The choice is reported either way, in `warnings`.

## What it costs: a file ten times larger

`repack` stores the parts it rewrites, because two implementations must write the same bytes and no
two compressors promise that (ADR 0008). Until now that cost nothing worth naming. It does now:

| | bytes |
|---|---|
| `legacy-python-docx-default.docx` as it is | 36,810 |
| after repair | **381,937** — 10.4× |
| its `word/styles.xml`, deflated in the original | 12,147 |
| the same part, stored | 349,502 |
| the four rewritten parts, stored | 359,858 |
| the same four, had they been deflated | 14,807 |
| so the file, had they been deflated | ~36,886 — the size it started at |

The whole growth is one part. python-docx ships a 349 KB default styles part that deflates to 3.5%
of itself, and a repair has to rewrite it because its styles are missing complex-script twins.

A smaller, less style-heavy file barely moves: the docx-js file measured on 2026-09-18 goes from
8,797 to 11,483 bytes, 1.3×.

### What was decided

Ship this, and say so plainly in `references/repair.md`, both command-line guides and both scenario
pages: the file comes back bigger, and opening it in Word and saving compresses it again.

Then write a deflate of this project's own — fixed Huffman codes and a greedy match search, defined
exactly enough that both implementations produce the same bytes by construction, rather than by
hoping two libraries agree. The target is the row above: a repaired file about the size of the one
it came from. That is the next piece of work, and it has a number to hit.

Storing was the right first choice — it made the repair correct and provable before it made it
small, and the measurement above is what says the next step is worth taking.

## Tests

`tests/test_repair.py` grows to 21, gate `repair-changes-only-what-it-names`: a run with no marks at
all, a Latin property without its twin, the font chosen three ways (asked for, the document's own,
the default) and reported, a Symbol bullet, and — unchanged from the first two codes — the text
compared character for character, every untouched part's bytes kept, a file whose only findings are
ones this version does not repair left alone, idempotence, and the refusals.

`tests/test_js_parity.py` runs the same six command lines through both implementations. The repaired
`legacy.docx` has the same sha256 from Python and from Node.

269 tests pass.
