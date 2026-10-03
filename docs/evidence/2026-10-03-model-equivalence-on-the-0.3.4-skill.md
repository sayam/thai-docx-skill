# 2026-10-03 — model equivalence on the skill of 0.3.4

What this proves: the two sentences 0.3.4 changed in SKILL.md — what the answer after a repair
names, and that a setting asked for without a value is never asked about — still lead three
models to the file each request of [the last record](2026-09-30-model-equivalence-on-the-0.3.3-skill.md)
asks for, and Sonnet and Opus pass every case. What it also shows, and does not prove: on Haiku,
after a repair the page breaks are named in ten runs of twelve on the sentence as merged, where
the old sentence had four of six under the same rule; and after "change the font and add page
numbers" Haiku still asks where the page numbers go in one run of six, on either wording. Each
cell is one to six runs, a sample and not a measure.

Environment: as in the last record, on Claude Code 2.1.288. Models: `claude-haiku-4-5-20251001`,
`claude-sonnet-5-5` and `claude-opus-5-5`. Each `claude -p` was capped at US$1. Every turn was
billed to a Console API key (its credential, as Claude Code reports it, was `ANTHROPIC_API_KEY`,
in all 72 turns of the first set, 6 of the second and 18 of the third). The skill was packed once
per set and the same zip given to every run; the traces are the maintainer's working copy and are
not part of the repository.

## What an agent reads now that it did not

- **SKILL.md, "change the font"**: "Ask that one value, and nothing else in that message: a
  setting asked for without a choice ("add page numbers") is never asked about and its choices
  never offered — it takes its default, and you say which (page numbers: top-right)." (V34-04)
- **SKILL.md, after a repair**: "your answer names three things: the new file; the font `repair`
  chose (its `font` warning); and that page breaks can move (its `layout` warning — say that,
  การแบ่งหน้าอาจเลื่อน in Thai, never page size or page numbers)." (V34-03)

Each is the second wording tried; the first of each is under *Three sets*.

## The files the requests ask for

No golden has moved since 0.3.0; the hashes are those of the last record.

| case | flags | sha256 |
|---|---|---|
| *sample*, *trigger* | none | `cc1e73ba…c350` (= `tests/golden/sample-default.docx`) |
| *thesis* | `--heading-numbers --page-numbers bottom-center` | `0b64a9d6…77d2` (= `tests/golden/thesis-text.docx`) |
| *change* | `--size 14 --page-numbers` | `be3282d3…8d82` |
| *fontother* | `--font "Angsana New"` | `fc0d003e…8ea5` |

## What is scored more strictly than before

- ***repair***: the last records passed a run that named the font and said anything with "page"
  or "หน้า" in it; the miss they recorded — "may change where letters and lines fall" — failed only
  because it had neither word. This record asks for the page breaks themselves: a line that names
  them (`page break`, การแบ่งหน้า, ขึ้นหน้า, ตัดหน้า) and says they move. "Page size may shift",
  "page numbers may move" and "some pages change position" are misses under it, where the old
  rule passed them. The old rule's verdict is kept beside each run.
- ***vague*, *vaguefirst***: the last records took a question about the page numbers as a second
  question only on a line of its own. The first set had Haiku ask both on one line — "…หรือฟอนต์อื่น?
  และเลขหน้าไว้ที่ไหน — top-right, top-center หรือ bottom-center?" — and pass. Now a question about where
  they go, or two of the three positions offered, is a second question wherever it stands; a
  statement of the default ("เลขหน้าจะใส่มุมขวาบน") is not. Whether the run says the default at all
  is shown, not scored.

## Three sets

**The first set** (zip `aade9617…143d`, 59 runs: the 53 of the last record, with Haiku's *vague*
and *repair* at six each) had the first wording of both sentences: "pass on every warning in its
own words: `layout` means "page breaks can move", said so, not as a change of letters or lines"
and "…is never a question — it takes its default, and you say which (page numbers: top-right)".
Every case passed but two Haiku cells. *repair*, two of six: one run gave no layout warning at
all; one named the page breaks but not the font; one said the page size may shift a little
(ขนาดหน้ากระดาษอาจเลื่อนนิดหน่อย); one said the page numbers may move (เลขหน้าอาจเลื่อนได้) — four of six
under the old rule, the rate of the records before. *vague*, five of six: the run above, which
asked the font and the position in one line. US$3.92.

**The second set** (zip `3fde553d…519e`) replaced the repair sentence with the one above — the
three things named, and the Thai words — and ran Haiku's *repair* again, six runs: six of six,
each naming the new file (`broken-fixed.docx`, `broken_fixed.docx` or `fixed.docx`), TH Sarabun New and
การแบ่งหน้าอาจเลื่อน or "page breaks อาจเลื่อน". US$0.24.

**The third set** (zip `026df156…ed5f`, the skill as it is merged) replaced the font sentence
with the one above — "never asked about and its choices never offered" — and ran Haiku's *vague*
and *repair* again, six each. *vague*, five of six: the miss asked the font, then "เลขหน้าจะใส่มุมขวาบน
(ค่าเริ่มต้น) ได้ไหม หรือจะที่กึ่งกลางบน / กึ่งกลางล่าง?" — the default named and the choices offered as a
question. *repair*, four of six: the two misses said "some pages changed position" and "the
document's page positions may shift" (ตำแหน่งหน้าของเอกสารเลื่อนไป), the font and the new file named;
both pass the old rule. US$0.73. All three sets, US$4.89.

## What came back

The eleven requests of the last record, none new. The Haiku cells of *vague* and *repair* are the
third set's; every other cell is the first set's.

| case | Haiku | Sonnet | Opus |
|---|---|---|---|
| *sample* | 1 of 1 exact | 1 of 1 | 1 of 1 |
| *thesis* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *change*, two turns | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *trigger* | 3 of 3 exact | 1 of 1 | 1 of 1 |
| *vague*, two turns | 5 of 6 (first set, first wording: 5 of 6) | 1 of 1 | 1 of 1 |
| *vaguefirst* | 3 of 3, each loading the skill | 1 of 1 | 1 of 1 |
| *checkask* | 3 of 3 | 1 of 1 | 1 of 1 |
| *checkonly* | 3 of 3 | 1 of 1 | 1 of 1 |
| *repair* | 4 of 6, 6 of 6 under the old rule (second set, same wording: 6 of 6) | 1 of 1 | 1 of 1 |
| *fontlong* | 3 of 3 | 1 of 1 | 1 of 1 |
| *fontother* | 3 of 3 exact | 1 of 1 | 1 of 1 |

**Twenty-three of twenty-three files byte for byte what was asked. Sonnet and Opus passed every
case. On the sentences as merged, Haiku named the page breaks after a repair in ten runs of
twelve and named the font and the new file in all twelve; after "change the font and add page
numbers" it asked the font alone in five runs of six.** The second question Haiku still asks, and
the paraphrase of a warning it still makes, are the misses the records of 0.3.1, 0.3.2 and 0.3.3
each show once; the sentences lower neither to nothing.

## Shown, not scored

- **Two Haiku *repair* runs ran `repair broken.docx broken.docx` first** (one in the first set,
  one in the second). `repair` refused it — "the output is the file to repair; repair writes a new
  file, never over the one given (ADR 0037)", exit 2 — and each then wrote `broken-fixed.docx`
  and named it. The user's file was not touched; the control that held is the command's own
  (R3), not the sentence. No run of the third set did so.
- **"You say which":** of the Haiku *vague* runs on the sentence as merged, two of six said the
  page numbers would go top-right; four asked the font and said nothing of the page numbers.
  Every Sonnet and Opus run said it. The last records did not look at this.
- Haiku still lists the three fonts when it asks which, in one line; shown since the record of
  0.3.1 and not scored (the maintainer's ruling of 2026-09-29).

## The misses

- ***vague*, once in six, Haiku asked whether top-right would do and offered the other two
  positions**, after asking the font. The same kind of miss as in the last three records.
- ***repair*, twice in six, Haiku said pages or page positions may shift** and not that the page
  breaks move. It named the font and the new file. Under the rule of the last records, no miss.
