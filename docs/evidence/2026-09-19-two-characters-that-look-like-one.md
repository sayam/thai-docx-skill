# 2026-09-19 — two characters that look like one

Two open questions about the author's own text, answered together in
[ADR 0034](../adr/0034-two-characters-that-look-like-one.md): **ำ typed the long way**, and
**`&nbsp;`**. This is what was measured before deciding.

## The measurement

Python 3.13 `unicodedata`, on 2026-09-19:

```
U+0E33 ำ   decomposition: <compat> 0E4D 0E32
U+00A0     decomposition: <noBreak> 0020

"ท" + "ำ"        vs  "ท" + "ํ" + "า"
  NFC  makes them equal: False
  NFD  makes them equal: False
  NFKC makes them equal: True    ← by pulling ำ apart, not by joining the other two
  NFKD makes them equal: True    ← the same way
```

**The only normalisation that makes the two forms equal does it in the wrong direction.** It turns
every `ำ` in a thesis into `ํ` + `า`, which is the form WPS already draws in the wrong place
([record](2026-09-19-wps-writer.md)). Nothing in Unicode composes the pair back. So there is no
standard to point at for "make them the same", and inventing one would be the build editing a
thesis — which [ADR 0023](../adr/0023-fidelity-transformations-restated-again.md) exists to
prevent.

The build's `INVISIBLE` set was read at the same time: U+200B, U+200C, U+200D, U+2060, U+FEFF —
five characters, and U+00A0 is not one of them. A literal non-breaking space builds with no
finding and no warning, which is right: it is typography, not a character pretending to be
nothing.

## What changed

A **warning**, in both implementations, with the line number:

```
$ python thai_docx build long.md long.docx
line 3: ํ followed by า looks like ำ but is two characters; it is written as
        it stands and a search for ำ will not find it
```

The text in the document is untouched — `การทํางาน` goes in as `ก า ร ท ํ า ง า น` and comes out
the same nine characters. The test asserts that directly, not only the warning.

`&nbsp;` gets nothing new. `references/markdown.md` has said since 2026-09-18 that CommonMark
resolves it to one non-breaking space, and that sentence is the whole remedy; a warning on every
entity would fire on `&amp;` in documents that are correct.

## Held by

| test | what goes red |
|---|---|
| `test_sara_am_written_the_long_way_is_named_and_left_alone` | the warning stops firing, or the text stops being written as typed |
| `test_sara_am_written_the_long_way_is_read_the_same` | the two implementations disagree — the generated corpus never writes the long form, so these eight texts are put to both by hand |

Both were run red before the change and green after.

## What it did not cost

**No document's bytes move.** Nothing is written differently; only the report gained a line. The
goldens, the release oracle and the five-application checklist are untouched by this record — the
re-check ADR 0012 asks for before the next release is still owed for
[the task box](2026-09-19-a-box-every-reader-can-draw.md), and this changes nothing about it.

Two reviewer samples were rebuilt to confirm: `34d38e9beb4bcaf7` and `2157a31e156cc1c5`, the same
hashes as before the change, the second now carrying the new warning and the same bytes.

301 tests pass.
