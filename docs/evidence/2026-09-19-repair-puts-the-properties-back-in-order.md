# 2026-09-19 — repair puts the properties back in order

The last repair of v0.2's list. `repair` now clears five of the seven finding codes; the two it
leaves are the two [ADR 0032](../adr/0032-repair-rewrites-attributes-never-the-text.md) says it must
never touch, because touching them means touching the user's text.

## What was wrong, and what Word does about it

WordprocessingML fixes the order of a run's properties, a paragraph's, and the document's settings.
An element in the wrong place is not an error a reader reports — Word **ignores it**. A document can
carry `<w:b/>` that does nothing because it comes after something that should follow it, and nobody
is told.

```
$ thai_docx check out-of-order.docx
{"code": "order", "part": "word/document.xml",
 "message": "in a run's w:rPr, <w:cs> must come before <w:lang>"}
```

That one is this project's own concern twice over: `<w:cs/>` out of place is the mark that makes
Thai render as Thai, quietly not applying.

## The rule

> The elements the schema names are put in that order, **in the places they already occupy**.
> Anything the schema does not name keeps its own place.

The second half is the part worth stating. The checker skips an element it does not know — an
extension from some other program — so moving one would change more than the finding asked for:

```
<w:rPr><w:sz w:val="32"/><w:somethingElse/><w:b/></w:rPr>
→ <w:rPr><w:b/><w:somethingElse/><w:sz w:val="32"/></w:rPr>
```

`w:b` and `w:sz` swap into the first and third slots, which are the slots they already held between
them. `w:somethingElse` does not move.

Two children of one name keep the order they were written in — a stable sort — because
`<w:b w:val="1"/><w:b w:val="0"/>` and its reverse mean different things.

## A permutation is free

Reordering children rewrites the same bytes in a different order, so the part's length never
changes. That is what lets the repair walk every element in a part without recomputing offsets, and
it processes inner elements first — a `w:pPr` holds a `w:rPr`, and moving a whole child keeps the
order already put right inside it.

## Where it applies

Every `w:rPr` and `w:pPr` in the text parts, in `word/styles.xml` and in `word/numbering.xml`, and
the `w:settings` element itself — the same places `check.py` looks.

## Tests

`tests/test_repair.py` grows to 26, gate `repair-changes-only-what-it-names`:

- a planted order finding is repaired and the file checks clean;
- an element the schema does not name keeps its place;
- two children of one name keep the order they were written in;
- properties already in order are not touched at all — the same bytes back, and a count of zero.

`tests/test_js_parity.py` gains a package whose only fault is the order of a run's properties, run
through both implementations: the same bytes out of each.

## What repair now does, and what it will not

| code | |
|---|---|
| `1` compatibility mode | repaired |
| `2` the marks a Thai run needs | repaired |
| `3` proofing switched off | repaired |
| `5` the complex-script twins, fonts, bullets | repaired |
| `order` properties in the wrong place | repaired |
| `4` a word split across two runs | **reported** — merging runs is a change to the document's structure whose failure a test can miss; v0.3 |
| `invisible` zero-width and other invisible characters | **reported** — they are the user's text, and this project does not change that |

Both of the remaining two are held back for the same reason the repair exists at all: the
attributes are ours to fix, the text is the user's.
