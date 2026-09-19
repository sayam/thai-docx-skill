# 2026-09-19 — an English heading is a heading

The WPS re-check of the new task-list boxes found something the box was hiding. In
`sample-options`, built with `--align thai` and `heading-1: text-align: center`:

- **บทคัดย่อ** — centred, as the front matter asked.
- **Abstract**, the same level, the next page — **flush left**.

The maintainer's reading was the right one: if the Markdown asked for that, it is not a fault;
if it asked for both to be centred and only one obeyed, it is. The Markdown asked for both.

## What the file said

`tests/golden/thesis-options.docx`, before the fix:

```xml
<w:p><w:pPr><w:pStyle w:val="Heading1"/><w:numPr><w:numId w:val="0"/></w:numPr></w:pPr>
  … บทคัดย่อ
<w:p><w:pPr><w:pStyle w:val="Heading1"/><w:numPr><w:numId w:val="0"/></w:numPr>
  <w:jc w:val="left"/></w:pPr>
  … Abstract
```

Both are `Heading1`, whose style carries `<w:jc w:val="center"/>` from the front matter. The
English one then overrode its own style at the paragraph. **This is not a WPS difference** — a
paragraph property beats a style property in OOXML, so Word 365, LibreOffice and Google Docs all
draw it left too. It had simply never been looked at: the Thai and English abstracts sit two pages
apart, and no test compared them.

## Where it came from

`latin_jc`, and it was doing something right for something else. Under `--align thai` the document's
own alignment is `thaiDistribute`, which fills a line by spreading what is on it — correct for Thai,
which has no spaces between words, and wrong for English, where `(2024a)` comes out as
`( 2 0 2 4 a)`. So a paragraph with no Thai in it is given `left`.

A heading is a paragraph, so it was given `left` as well. The guard that was supposed to stop
this — "does this paragraph already set an alignment?" — only looked at the paragraph. A heading's
alignment lives in its **style**, which is exactly where `heading-1: text-align: center` puts it.

## The fix

A paragraph whose style fixes an alignment keeps it. The styles that do are the ones this skill
writes a `<w:jc>` into: **Heading1 … Heading6 and CodeBlock** — the headings from ADR 0020's
`text-align` (or `left` by default), CodeBlock because code is never distributed.

```python
STYLE_FIXES_ALIGNMENT = frozenset({"Heading" + str(n) for n in range(1, 7)} | {"CodeBlock"})
```

An ordinary Latin paragraph still gets `left`; nothing about Thai distribution changed. Both
implementations, one rule.

## Held by

| test | what goes red |
|---|---|
| `test_an_english_heading_is_aligned_like_its_thai_twin` | a Latin heading stops taking its style's alignment — the bug itself, with บทคัดย่อ and Abstract side by side |
| `test_the_styles_that_fix_alignment_are_the_ones_named` | the constant stops matching the styles that actually carry a `w:jc`, read out of `styles.xml` |
| `test_thai_distributed_leaves_a_paragraph_without_thai_alone` | updated: it used to require *every* Latin paragraph to carry `left`, which is what made the bug look correct |

The first two were run red before the change.

## What it costs

**The bytes of every document built with `--align thai` change.** Only those: the two goldens
without it are byte-identical.

| golden | bytes | sha256 |
|---|---|---|
| `sample-all-flags` | 36,646 → **36,566** | `65cf972b62a1…` |
| `thesis-options` | 207,614 → **207,494** | `3d9e9ebd7c9b…` |
| `sample-default`, `thesis-text`, `thesis-layout` | unchanged | — |

The file gets *smaller*: the fix removes a property rather than adding one.

This is the second byte change owed to the five-application check of ADR 0012 before the next
release, after [the task box](2026-09-19-a-box-every-reader-can-draw.md). Both are now in.

303 tests pass.

## What the same check confirmed

The boxes of ADR 0033 draw in WPS Writer: `■` for a checked item and `□` for an unchecked one, in
the body of `sample-options`, on the machine that has no Microsoft symbol font. The change that
record argued for does what it said it would.
