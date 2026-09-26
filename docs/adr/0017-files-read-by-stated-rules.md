# 0017 — The checker and the build read files by stated rules, not by a library's habits

- Status: accepted
- Decided: 2026-09-15

## Where it came from

Holding the two implementations of 0008 to the same output on damaged and
unusual input turned up three places where each had simply inherited what its
platform does:

- **Zip packages.** A flipped bit made an entry inflate one byte past its
  declared size: Python's `zipfile` stops at the declared size and the checksum
  of what it kept still matches, so the entry passed; the JavaScript reader
  refused it. A comment length that ran past the central directory was cut short
  by `zipfile`, which then listed four entries of nine.
- **XML parts.** Expat, the parser behind the Python checker, accepts a name
  character by its own tables, which differ from the XML 1.0 fifth-edition ranges
  the JavaScript reader had used: `<aฯ/>` (U+0E2F) is refused by expat and allowed
  by those ranges. Expat also refuses `a:-b`, and bindings of the reserved `xml`
  and `xmlns` prefixes and namespaces, which the reader had let through.
- **Image paths.** Python's `Path.resolve()` follows a symbolic link before it
  applies `..`; Node's `path.resolve()` removes `..` as text first. For
  `![](link/../x.png)` the two looked at different files — and the limit of 0011 §4
  is judged on that file. Python 3.11 also raises `RuntimeError` on a symlink
  loop [S30], which would crash the command with a traceback.

What a library does with damaged or unusual input is rarely documented and can
change between releases; the Python side runs on 3.11 and later. A verdict that
depends on it cannot be the same on every runtime.

## Decision

Each implementation reads with its own short code, by these rules. The Python side
takes only raw deflate decoding (`zlib`) and XML parsing (expat) from its platform,
and the JavaScript reader is held to both.

**Zip packages** — the layout of APPNOTE 6.3.10 [S27]. Entries are written stored,
in the order given, version 20, dated 1980-01-01 00:00, attributes `0o600 << 16`,
the UTF-8 flag only for a non-ASCII name, no extra fields or comments. Reading:
anything that breaks rules 1–5 is "not a zip package"; 6 and 7 are their own
findings; anything that breaks 8–10 is "entry cannot be read".

1. At most 64 MiB of the file is read; a longer file is refused by size.
2. The end record is the last 22 bytes when they carry its signature and no
   comment; otherwise the last signature in the final 65,557 bytes whose comment
   ends exactly at the end of the file.
3. When a zip64 locator sits just before the end record, the zip64 end record
   must sit just before the locator, and its count, size and offset are used.
   No 64-bit value may reach 2⁵³.
4. Bytes before the archive are allowed; offsets shift by their length, which may
   not be negative.
5. The central directory's records follow one another with no gap and fill it
   exactly, each with its signature, and their number is the one the end record
   gives. A name with the UTF-8 flag must be valid UTF-8; without it, it is read as
   code page 437. A zip64 extra field supplies, in order, the file size, compressed
   size and offset that read `0xFFFFFFFF`, and must lie inside its entry's extra
   data.
6. A name that appears twice is refused — two readers may pick different copies.
7. Declared sizes are capped as 0011 §7 says, before anything is inflated. Only
   `.xml` and `.rels` entries are read; one that is encrypted, or compressed by
   anything but store or deflate, is refused.
8. The local header has its signature, lies inside the file, and repeats the
   central directory's name byte for byte; the data follows it inside the file.
9. A stored entry's two sizes are equal. A deflated entry is decoded as RFC 1951
   [S28] with zlib's strictness — an over-subscribed or incomplete Huffman code is
   refused, except a single one-bit literal/length or distance code [S29] — must
   reach its final block within its compressed bytes, and must give exactly its
   declared size.
10. The CRC-32 of the bytes equals the central directory's.

**XML parts.** The JavaScript reader accepts exactly what expat, reading with
namespaces, accepts [S31]. Where that is a table — which characters may start or
continue a name — the table is measured from expat by
`tools/measure_xml_names.py`, committed as `assets/xml-names.json`, and
re-measured by the test suite on every run, so a different expat shows up as a
red test rather than as two verdicts.

**Nesting.** Neither implementation reads by recursion where its input sets the depth.
(**Later, 2026-09-26:** what holds for the Markdown is a limit, not the absence of recursion — the
parser finalises blocks recursively, and the 100-deep cap is what keeps it within the stack; the
checker's comparison of run properties, which did recurse as deep as the input went, reads with a
stack of its own since ADR 0040.)
The JavaScript XML reader keeps open elements on a stack, so it reads any depth expat
reads. Markdown blocks nested more than 100 deep, or inline formatting nested more than
100 deep within a block, stop the build at the line where the limit is crossed: every
later step walks the tree recursively, and a stack overflows at a depth that differs by
runtime — at 1,000 nested blockquotes Python raised `RecursionError` while Node answered.

**Image paths.** A path is walked component by component, as the file system
walks it: a symbolic link is followed where it stands, `..` is taken from what is
already resolved, and a component that does not exist — or a link past the
fortieth — stays as written. An image path that is absolute stays absolute.
Containment (0011 §4) is judged on the walked path.

Left out on purpose: repairing a damaged package; reading entries by their local
headers alone; a hand-written XML parser on the Python side.

## Why

The checker's value is a verdict that does not depend on where it ran, and the
build's is a file that does not depend on it either. Rules written down can be
ported and tested; a library's handling of damage can only be imitated, one
release at a time. Refusing what Word never writes — duplicate names, directories
that do not add up, entries longer than they say — costs no real document and
closes the gap where two readers see two different files. Walking a path the way
the file system does is also the only reading under which the image limit of 0011
means what it says.

## Expires when

A document from a real office application is refused under these rules, or a
supported Python's expat accepts different names; the rule is then changed in
both implementations through a new record.
