# 0032 — Repair rewrites the attributes that break Thai, never the text

- Status: accepted
- Decided: 2026-09-18
- Supersedes: nothing; it takes up what 0006 left for v0.2

## Where it came from

0006 set the scope: the skill builds Thai documents and **checks** ones it did not write, and said
repair would wait for v0.2 and a corpus to test it against. Since then the checker has been proved
both ways — on planted defects and on files other generators produced
(`docs/evidence/2026-09-15-javascript-matches-python.md`) — and a user who asks for a check asks,
next, for the fix.

Two measurements made on 2026-09-18 say who needs that fix and why nobody else will supply it:

- **Word does not repair a file it did not type.** Saving a file another program wrote adds
  `<w:lang w:val="en-US"/>` to every run and still writes no `<w:cs/>`; an edit made through an
  assistant that runs inside Word behaves the same
  ([record](../evidence/2026-09-18-word-does-not-repair-what-it-opens.md)).
- **A general assistant asked for a Thai `.docx` marks none of its runs as Thai** — 343 of 343 runs
  on a plain report, 584 of 584 on a thesis
  ([record](../evidence/2026-09-18-the-same-source-three-assistants.md)).

So broken Thai documents keep arriving, and opening them in Word is not a way out. This record
answers what a repair may touch.

## Decision

- **`thai_docx repair IN.docx OUT.docx` writes a new file.** Never in place: the write limits of
  ADR 0030 §3 stand, and a user who loses the original has lost the content.
- **It changes only the WordprocessingML that makes Thai render wrongly**: the compatibility mode,
  a run's complex-script marks, a missing complex-script twin of a Latin property, a bullet level's
  font, `<w:noProof/>`, and the order of properties the schema fixes. Findings `1`, `2`, `3`, `5`
  and `order`.
- **It does not change a character of the document's text, and no flag relaxes that.** The
  paragraph-by-paragraph comparison the build runs against its Markdown (ADR 0023) runs here between
  input and output; a difference of one character refuses the write.
- **A word split across two runs (code 4) is reported, not merged.** Merging changes the document's
  structure in a way a test can miss — a bookmark, a comment anchor or a field character between the
  runs — so it waits for a corpus that shows the merge safe. v0.3.
- **Invisible characters are text.** They are reported, with the character named, and never removed.
  There is no `--strip-invisible`, in this version or a later one.
- **Everything else comes through untouched, byte for byte** — parts this skill does not understand,
  media, and the compressed bytes of every entry it did not rewrite.
- **A file it cannot read is refused, not repaired**: a damaged package, a DOCTYPE, or a package
  past the size caps of ADR 0030 §9 behave exactly as they do for `check` today.
- **Both implementations write the same bytes** (ADR 0008), and repairing a repaired file changes
  nothing.
- **The report says what was repaired, what was left, and every decision the repair had to make** —
  above all the font chosen for a missing complex-script twin.

Left out on purpose: merging split runs, removing invisible characters, embedded fonts, tracked
changes, content controls, fields, document properties, and any change of layout or style beyond
those listed. None of them is what makes Thai wrong, and each would need an oracle this project
does not have.

## Why

A document arrives from another program with the user's own work in it. The one thing the project
cannot afford is to hand back a file whose text differs from the one it was given, quietly. So the
repair is defined by what it may touch rather than by what it may achieve: everything on the list is
an attribute Word reads and a person never wrote, and everything off the list is either content or
somebody else's decision.

Writing a new file rather than editing in place, and copying untouched entries byte for byte, keep
the failure small: the worst outcome is a file that still needs work, beside an original that has
not moved.

One consequence is worth naming, because it is not a text change and is still visible: setting the
compatibility mode to 15 reflows the document, which can move page breaks. That is the point of the
setting, and the report says so before the user sends the file to anyone.

## What it costs

The packer has to grow. `package.pack` writes every entry **stored**, with a fixed date — right for
a file built from nothing, wrong for repair. Measured on
`tests/fixtures/legacy-python-docx-default.docx`: 17 entries, 826,679 bytes of content, packed to
34,818 by deflate. Storing them would hand the user a file about twenty-four times larger than the
one they gave. Repair needs a packer that copies an untouched entry's compressed bytes as they are —
method, CRC and sizes — and only writes the parts it rewrote, in `package.py` and `js/10-zip.js`,
with a round-trip test of its own: read a file, write it back unchanged, get the same bytes.

## Expires when

Merging split runs is shown safe on a corpus (that record is v0.3's), repair needs to change text to
be useful, a format other than `.docx` arrives, or the checker gains a finding whose repair this
record does not cover.
