# 2026-09-18 — the build names what it did not write

The second batch from the adversarial reviews of 2026-09-18: the sixteen claims left after the four
defects of the first batch were fixed. Thirteen reproduced here, one was already false, two are the
same defect seen twice, and two need a decision rather than a patch.

What the thirteen have in common is not a fault in the bytes. It is **silence**: a document came out
missing something a reader would want, and the build said `ok: true`, `warnings: []`.

## What was silent, and now is not

| what happened | now |
|---|---|
| `![](p.png)` — a picture with nothing between the brackets | `line N: the image 'p.png' has no text between the brackets of ![]; a reader who cannot see it is told nothing` |
| `#` then `###` — a level missing from the outline | `line N: a heading of level 3 follows one of level 1; the contents and a screen reader read the levels in order` |
| `[unused]: https://x.example` — a link definition nobody refers to, dropped by CommonMark itself | `line N: the link definition [unused] is never used; it is not written into the document` |
| `ตาราง: ผลการสำรวจ` just before a table — the Thai words where the prefix has to be `Table:` | `line N: a caption is written 'Table:' in English, in every language; this paragraph is kept as text` |
| a message past the 20,000-character cap, with `thai-docx grill` in the part that was cut | `the message was read to its first 20000 characters; N were not read, and the phrase may be among them` |

None of them refuses a build, and none changes a byte of any document: the thesis fixture's archive
has the same sha256 as before, `b7aab940…`, and every golden is unchanged.

## Why each one is worth a line

**The empty alt** (GROK-10, composer-07). `descr=""` is what a screen reader is given, and a thesis
or an official document that has to pass an accessibility check fails on it. The skill cannot invent
the description; it can refuse to let the author not notice.

**The heading jump** (GROK-11). The contents field reads levels in order, so a jump leaves a gap in
the table of contents as well as in the outline. Finding it needed a line number that heading blocks
did not carry — paragraphs, tables and directives had one and headings did not — so both parsers now
record it. That is the only structural change in this batch.

**The unused link definition** (GROK-04). CommonMark drops a definition nobody refers to, which is
correct and quiet. But `references/markdown.md` promises "Nothing is dropped silently", and a
footnote in the same position is *refused* with exit 2. A URL vanishing while a footnote stops the
build is an asymmetry the reviewer was right to name. It is a warning rather than a refusal because,
unlike a footnote, a definition takes no room in the document either way.

**The Thai caption prefix** (GROK-05). A Thai writer reaches for `ตาราง:`; the prefix is `Table:`,
in one language, so that one rule holds for everyone. Before this, `ตาราง: ผลการสำรวจ` above a table
became an ordinary paragraph and the table lost its number, with nothing said. The warning fires
only where a caption would have gone — the same words in the middle of a page stay ordinary text and
stay quiet.

**The cap that said nothing** (GROK-07, GROK-14, composer-02, composer-08). ADR 0029 caps the
message at 20,000 characters, which is a decision, not a defect. But the phrase may be in the part
that was dropped, and the answer the agent then reads is `mode: "build"` — indistinguishable from a
user who never asked for the interview. The cap stays; it now says when it bit, and SKILL.md tells
the agent the number.

## Two the code was told to do, and did

**`Documents with no Thai text are not for this skill`** (GROK-13) — SKILL.md said that, and `build`
happily builds an English document. The sentence now reads: *a document with no Thai in it needs
nothing this skill adds; build one only if asked to.* Which is what the code does, and what a user
who asks for one should get.

**The troubleshooting pages said the phrase needs a hyphen** (composer-04). True until this morning;
false since the space spelling was fixed. Both languages now say a hyphen, an underscore or a space.
Drift this project made in its own fix, six hours old, found by a reviewer reading rather than
running.

## Two left for a decision, not patched

- **`ำ` (U+0E33) against `ํ` + `า`** (GROK-12). The two spellings produce different bytes:
  `34d38e9b…` and `2157a31e…`, reproducing the reviewer's hashes exactly. ADR 0023 says the text is
  compared after NFC, and NFC does not compose these — U+0E33 is a composition exclusion. Making
  them equal means normalising beyond NFC, which is a new decision about the user's text and belongs
  in a record, not in a patch.
- **`&nbsp;` becomes U+00A0** (composer-03). CommonMark resolves entities; the fidelity check
  compares against what the parser read, so it passes. A user who expects the seven characters they
  typed gets one invisible character instead — and the checker's own `invisible` finding is about
  exactly that kind of character, though not this one. Also a decision about text, also a record.

Both are written up here so the next reader does not have to rediscover them.

## Tests

- `tests/test_build.py::test_the_build_names_what_it_did_not_write` — each of the four build
  warnings fires where it should and stays quiet where it should not, including the Thai caption
  words away from any table.
- `tests/test_grill.py::test_a_message_read_only_in_part_says_so` — a message five characters past
  the cap says so and counts them; a short one carries no `warnings` key at all.
- Three existing fixtures gained alt text, because their subject is regions and captions rather than
  images, and one example in `references/chapters.md` did too — documentation should model what the
  build asks for.
- `tests/test_oracle_set.py` now allows the outline jump in `sample.md`: that fixture goes from level
  2 to level 5 on purpose, to exercise both in one file, and its bytes are the goldens'. The test
  pins it to exactly one such warning rather than ignoring the class.

229 tests pass; ruff, ESLint and the gates doctor are clean; both implementations produce the same
warnings, checked at the command line for all five.
