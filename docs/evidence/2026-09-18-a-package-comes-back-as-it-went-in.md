# 2026-09-18 — a package comes back as it went in

The first step of v0.2's repair, and the one the rest waits on. [ADR 0032](../adr/0032-repair-rewrites-attributes-never-the-text.md)
says everything a repair does not touch "comes through untouched, byte for byte". Nothing in the
project could do that.

## What was in the way

`package.pack` writes every entry **stored**, with a fixed date. That is right for a file built from
nothing — ADR 0017 wants the same input to give the same bytes — and wrong for a file that arrives
from somewhere else. Measured on `tests/fixtures/legacy-python-docx-default.docx`:

```
the file as it is                                36,810 bytes
the same 17 entries, all stored by pack()       828,671 bytes   ← 22.5× larger
```

A user who sent a document with photographs in it would get it back many times the size, for a
repair that touched one XML part.

## What was added

`package.repack(bytes, entries, replace)` — and `repackZip` beside it in JavaScript. The package
again, in the order it had:

- an entry named in `replace` is written anew and **stored**;
- **every other entry keeps the bytes it already had** — its compressed payload copied without being
  inflated, with its method, its checksum, its two sizes, its DOS date and time, its "version made
  by" and its external attributes;
- a name that is not in the package is refused, because a typo would otherwise leave the file
  unchanged and say nothing.

Stored rather than deflated for the reason ADR 0008 gives: two implementations must write the same
bytes, and no two deflate libraries promise that. What a repair rewrites is XML of a few tens of
kilobytes; what it leaves alone — the media — keeps the compression it came with.

## What it does

Every package this repository holds, written back with nothing replaced, comes out **byte for byte
the file that went in**: five goldens this project built, and the two fixtures other generators
wrote.

That last part took two rounds. The first attempt differed by exactly seventeen bytes on each legacy
fixture — one per central directory record, the high byte of "version made by": the original said
Unix, the rewrite said MS-DOS. Preserving that field, and the external attributes beside it, closed
it. Worth recording because it is the shape of the whole problem: a package carries more about
itself than its contents, and a repair that forgets any of it hands back a file that is not quite
the one it was given.

## Tests

`tests/test_repack.py`, gate `repack-keeps-what-it-did-not-write`:

| test | what it holds |
|---|---|
| `test_a_package_written_back_unchanged_is_the_same_bytes` | over all seven packages, parametrised |
| `test_a_rewritten_part_is_stored_and_the_rest_keeps_its_compression` | the rewritten entry is stored and reads back; every other entry's **raw** bytes, method, checksum and date are the ones it had; the result opens in Python's `zipfile` with the same name list and passes `testzip()` |
| `test_storing_everything_is_what_repair_must_not_do` | the 20× figure, as a test rather than a sentence in a record |
| `test_repacking_a_repacked_package_changes_nothing` | idempotent, as ADR 0032 requires of the repair above it |
| `test_a_name_the_package_does_not_hold_is_refused` | the typo case |
| `test_both_implementations_write_the_same_package` | Python against JavaScript, over all seven, with and without a replacement |

248 tests pass.

## What this is not yet

It is the container, not the repair. Nothing yet decides *what* to rewrite: `repack` is given the
parts and writes the file. The finding-by-finding work of ADR 0032 §2 — the compatibility mode, the
complex-script marks, the missing twins, the bullet fonts, the property order — comes next, and it
now has somewhere to put its output.

Two limits worth naming before they surprise someone:

- **Extra fields are dropped.** A rewritten package carries no per-entry extra fields; offsets move
  when a part changes size, and a zip64 pointer left in place would be wrong. Nothing in a `.docx`
  this project has met depends on them, and the size cap (64 MiB) is far below where zip64 begins.
- **A data descriptor is not written.** Sizes and checksums go in the headers, as `pack` has always
  written them.
