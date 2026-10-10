# 0043 — A dot that closes a Thai character is Thai to the soft break after it

- Status: accepted
- Decided: 2026-10-10
- Amends: [0023](0023-fidelity-transformations-restated-again.md) transformation 1, which read
  *"A soft line break with no rendered text before or after it in its paragraph becomes nothing,
  and so does one between two Thai characters. Any other becomes one space."*

## Where it came from

The release review of 0.3.1 found that a Thai abbreviation wrapped at its dot, `พ.` at the end of
one line and `ศ.` at the start of the next, became `พ. ศ.` in the document. Transformation 1
of 0023 joins a soft break only between two Thai characters, and `.` is not one. The fix moves
the bytes a build writes, so it waited for 0.3.5, the version in which they move.

## Decision

Transformation 1 becomes: a soft line break with no rendered text before or after it in its
paragraph becomes nothing, and so does one between two Thai characters, **or between a Thai
character followed by `.` and a Thai character**. Any other becomes one space. The neighbour
is the adjacent text (empty text is skipped); the Thai character before the `.` may be in
another run (`**พ**.`), but not across an image, a hard break or another soft break.

`พ.` ↵ `ศ.` is `พ.ศ.`; `ปี พ.ศ.` ↵ `๒๕๖๙` is `ปี พ.ศ.๒๕๖๙`, as Thai digits are Thai
characters; `พ.ศ.` ↵ `2569`, `Mr.` ↵ `สมชาย` and `ก..` ↵ `ข` keep their space. A sentence
a writer closes with a dot joins too: `ครับ.` ↵ `ต่อไป` is `ครับ.ต่อไป`. A writer who wants
the space keeps the two on one line.

Left out on purpose: the comma. `สวัสดี,` ↵ `ชาวโลก` stays `สวัสดี, ชาวโลก`, as Thai writes a
space after a comma, and the test of the first build has said so since 2026-09-15. Other
punctuation that closes Thai (`)`, `"`, `ฯ` is already Thai) is not part of this rule.

## Why

CommonMark lets a soft break render as a space [S8] where Thai puts none between words or
inside an abbreviation, which is why 0023 joins two Thai characters. A Thai abbreviation is
letters and dots with no space, and wrapping a long line in the Markdown must not change the
text, which is the promise of 0023's transformation 1. The fidelity check reads the same
inline text, so what the document holds is still compared character for character.

## Expires when

A Thai writing convention that a writer of this skill's documents follows needs a space after
a dot closing a Thai word, or a comma that joins, and a test shows it.
