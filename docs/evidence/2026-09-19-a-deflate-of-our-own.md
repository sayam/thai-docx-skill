# 2026-09-19 — a deflate of our own, so a repaired file is the size it was

Yesterday's record measured the cost of repairing a document: a python-docx file of 36,810 bytes
came back as 381,937, because the parts a repair rewrites were **stored** rather than compressed
([the measurement](2026-09-18-repair-marks-thai-and-fills-the-twins.md)). Storing was not laziness;
it was the only way two implementations could write the same bytes, which ADR 0008 requires. No two
compression libraries promise the same output — zlib's depends on its version, its level and its
strategy — so the project could not call one from Python and another from JavaScript and expect the
sha256 to match.

The answer is to stop borrowing a compressor and to define one.

## What was written

`skills/thai-docx/scripts/thai_docx/deflate.py` and `js/11-deflate.js`: a raw deflate stream, the
same from both, because every choice a compressor is free to make is fixed in the module:

| the choice | what this project fixed |
|---|---|
| block type | fixed Huffman (`BTYPE=01`, RFC 1951 §3.2.6). A dynamic tree is a second thing two implementations would have to build identically, for a gain not needed here |
| finding matches | a chained hash of three bytes, 15 bits wide, over a 32,768-byte window |
| how far to look | at most 128 links of the chain, from the most recent position back |
| which match wins | the longest; the nearest of equal length, since the walk only improves on a strictly longer one |
| when to take it | as soon as it is found — greedy, never lazy |
| block length | closed after 65,536 bytes of input |
| the end | an empty final block, so the writer never has to know which block will be the last |

It is not the fastest compressor and it is not the smallest. It is the one both implementations
run to the same bytes **by construction**, rather than by hoping two libraries agree.

## What it does

| | bytes | of the original |
|---|---|---|
| `word/styles.xml` from the python-docx fixture | 349,458 | |
| this deflate | 14,257 | 4.1% |
| zlib at level 6, for comparison | 12,147 | 3.5% |

Within a fifth of zlib, on the part that mattered, in 0.8 seconds.

And the file the user gets back:

| | bytes |
|---|---|
| `legacy-python-docx-default.docx` | 36,810 |
| repaired yesterday, everything stored | 381,937 — 10.4× |
| **repaired today** | **39,437 — 1.07×** |
| the docx-js file from 2026-09-18, repaired | 8,968 — 1.02× |

The row yesterday's record set as the target was "about the size it started at". That is what it is.

A part is stored rather than compressed when compressing would make it larger — which is what
happens to bytes with no pattern in them, and to a part that is already compressed.

## Three bugs, and what each one taught

Written from RFC 1951 and tested against zlib's inflate, this took three corrections, each of which
is now a test:

1. **The stream never ended.** Every block was written with `BFINAL=0` and nothing closed the last
   one; zlib said "incomplete or truncated stream". The fix is the design above — an empty final
   block — which is simpler than tracking which block turns out to be last.
2. **A match ran past the end of the input.** The quick check that compares the byte just past the
   best match so far read `data[i + best_len]` without knowing that `i + best_len` could be the end.
   A match is now bounded by `size - i` before the search begins.
3. **A negative index wrapped.** The hash chain ends at `-1`, and the window limit `i - 32768` is
   negative early in the input, so `-1 > limit` was true and the search read `data[-1 + best_len]` —
   which Python reads from the end of the buffer instead of failing. zlib then said "invalid
   distance too far back". The chain now ends on `at >= 0` as well.

The third is the one worth keeping: a language that wraps a negative index turns a logic error into
a silent wrong answer, and only a reader outside the project — zlib — caught it.

## Tests

`tests/test_deflate.py`, gate `deflate-is-defined-not-borrowed`, over ten shapes: nothing, one byte,
two bytes (shorter than the shortest match), one repeated pair, every byte twenty times, a run
longer than the longest match, this project's own source, a styles part from another program, bytes
with no pattern, and a match that reaches the end of the input.

| test | what it holds |
|---|---|
| `test_zlib_inflates_what_this_deflates` | every shape, through zlib |
| `test_both_implementations_compress_to_the_same_bytes` | every shape, Python against JavaScript |
| `test_the_skills_own_reader_inflates_it_too` | through the JavaScript implementation's own `inflateRaw`, so a file one writes the other can read |
| `test_it_is_worth_doing_at_all` | under 5% of the input, and within half again of zlib |
| `test_bytes_with_no_pattern_are_not_made_much_worse` | a compressor that doubled them would be a bug |

293 tests pass.

## What this is not

It is not a general-purpose compressor and nothing else in the project uses it: `build` still packs
with stored entries and a fixed date, because a document built from nothing should be the same bytes
on every run and its parts are small. This exists for `repair`, where the input is somebody else's
file and its size is theirs, not ours.
