# 0037 — Repair puts a document's own numbering back, and asks which kind it is before it starts

- Status: accepted
- Decided: 2026-09-20
- Supersedes: 0032
- Extends: [0036](0036-who-counts-is-one-switch.md) (who counts is one switch, and a written number
  is generated matter), [0023](0023-fidelity-transformations-restated-again.md) (the author's own
  words are untouched), [0030](0030-script-limits-read-by-tests-in-both-implementations.md) (what a
  script may read and write)

## Where it came from

[ADR 0032](0032-repair-rewrites-attributes-never-the-text.md) drew repair's line at the attributes
that break Thai: *it changes no character of the document's text, and no flag relaxes that.* Its
own "Expires when" named the condition that has now arrived — **repair needs to change text to be
useful.**

On 2026-09-20 the maintainer settled what the skill promises over a document's life, and it is the
promise that makes the line wrong:

- **The five-application contract covers the document as the skill hands it over**, built to be
  used as it is. That is the default: every heading, list and caption number is text the build
  wrote, identical in all five applications.
- **A reader who then edits that document keeps its format themselves** — the numbers do not
  renumber, and the skill says so plainly rather than letting them find out.
- **And when they bring the edited file back, repair should put the layout right**: re-run the
  numbers, bring a paragraph's indent and a run's font to the pattern the rest of the document
  already follows. That is what "usable as it leaves the skill" means once a document has a life
  of its own — and it is the hole this skill opened by writing numbers as text in the first place
  (rule 3: close the hole you opened yourself).

A document where the user typed `๒.๑` twice, or skipped `๒.๓`, or added a paragraph that is not
indented like its neighbours, is not a rendering fault an attribute can reach. Under 0032 the skill
could only hand it back untouched.

## Decision

**Repair reads the document's numbering first, and says which kind it is.**

| what it finds | what it means |
|---|---|
| `w:numPr` on a heading, a numbering definition tied to a heading style, `SEQ`/`STYLEREF` in a caption, `w:numPr` on a list item | the application counts — **automatic** |
| a number as text at the head of a heading, a caption or a list item, and none of the above | the build's kind — **written** |

**Where automatic numbering is present, repair chooses nothing.** It stops, writes no file, and
says what it found. The assistant asks the user which the document should be — the application
counting throughout, or written numbers throughout — and repair is run again with that answer.
One side or the other, never half: a document that renumbers its headings but not its captions
goes wrong in silence, which is what ADR 0036 refuses at build time and this refuses at repair
time. In doubt, no file is written (rule 4).

**Where the numbering is written, repair may rewrite the running numbers — and nothing else of the
text.** A running number is generated matter, the same runs the build writes (ADR 0036):

- the number at the head of a paragraph in a heading style, to the pattern the document's own
  headings follow;
- the label and number at the head of a caption paragraph;
- the marker at the head of an ordered-list item.

**Everything else is the author's words and is compared character for character, as before.** A
number anywhere but the head of one of those three paragraphs is the author's — a year, a
quantity, a version — and is never touched. Where the document's own pattern cannot be read,
because too few paragraphs of a kind are there to show one, repair leaves that kind alone and says
so rather than guessing.

**Besides the numbers it changes attributes only**, and to the document's own pattern, never to
this skill's defaults: the complex-script attributes 0032 already listed, plus a paragraph's
indent and a run's font and size where that paragraph departs from what the rest of its kind does.
The pattern is a majority of the document's own paragraphs of that kind; where there is no
majority there is nothing to bring it to.

**Everything else 0032 decided stands, unchanged:**

- a new file is written and the original is never touched, never overwritten;
- a word split across two runs (finding `4`) is reported, not merged, and invisible characters are
  reported, never removed;
- a file it cannot read — damaged, not a Word file, a DOCTYPE, past the size caps — is refused;
- both implementations write the same bytes, and repairing a repaired file changes nothing;
- untouched parts come through byte for byte.

**The report says every number it changed, with the paragraph it was in and what it was before.**
A user must be able to read back what the skill did to their document without opening it.

**Left out on purpose:** repair does not add numbering where a document has none, does not turn a
written document into an automatic one or the other way round (that is a rebuild from Markdown),
does not merge runs, and does not touch tracked changes, content controls, fields or document
properties.

## What ships first, and what is true until it does

This record is the decision; the work is owed and named in `ROADMAP.md`. Until it ships, repair
does what 0032 described — attributes only, not one character of text — and
`references/limits.md` says so in the present tense. No page may describe the renumbering as
something the skill does today.

The order the work goes in: the reading of a document's numbering kind (it is worth having on its
own, because it is what lets the assistant ask the right question), then the numbers, then the
indent and font.

> **Later (2026-09-26):** the first step shipped in 0.3 in `check`, which answers every document
> with `numbering`: `automatic`, `written`, `mixed` or `none`, and how many headings, captions and
> list items of each kind. `repair` still changes attributes only; the numbers and the indent and
> font remain owed.

## Why

- **Rule 3**: the skill answers for the hole it opened. Writing numbers as text is what makes an
  edited document drift, and leaving the user to renumber by hand is only half an answer when the
  skill can read the pattern and put it back.
- **Rule 1**: a file is usable as it leaves the skill. A document that has been edited and comes
  back is still a document this skill handed over.
- **ADR 0023's line is the one that holds**, and it was never "no text changes": it is *the
  author's own words are untouched*. A number the build would have written is generated matter,
  like a caption's label — 0036 says so for the build, and the same sentence is what makes this
  safe for repair.
- **0032's absolute rule was right for 0032** — it was written when repair could not tell a
  generated number from a typed one. Reading the document's numbering kind first is what changed.

## What this gives up, plainly

**A number that is not the author's and does not look like the document's pattern can still be
rewritten** — a heading whose number a user deliberately made different will be brought into line.
The report names every one, and the original is beside it untouched, which is the answer to being
wrong: the worst outcome is a file that needs work next to a file that has not moved.

**A document with no majority pattern gets less.** A short document with two headings cannot show
what its headings do; repair says what it did not do rather than deciding for it.

## Why not the alternatives

**Leave repair as 0032 wrote it and tell people to rebuild from Markdown.** Right whenever the
Markdown exists, and it is already what the documentation recommends. It is no answer for the user
who edited the .docx for a week and does not have the Markdown any more.

**Renumber by pattern wherever a number appears.** That reaches the author's own text — a year at
the head of a paragraph, a numbered term in a list of definitions — and there is no report long
enough to make that safe.

**Ask the user about each number.** A thesis has hundreds. The question that is worth asking is
the one about the document as a whole, and it is asked once.

**Repair in place, now that it changes more.** Never: the original untouched beside the new file
is what keeps a wrong decision cheap (0032, and rule 3).

## Expires when

A format other than `.docx` arrives, or a corpus shows that reading a document's numbering kind
cannot be done reliably enough to ask the right question — in which case repair goes back to
attributes alone and this record is superseded rather than quietly widened.
