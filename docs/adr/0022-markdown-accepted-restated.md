# 0022 — What Markdown v0.1 accepts, and what stops the build (restated)

- Status: accepted
- Decided: 2026-09-16
- Supersedes: 0010

## Where it came from

0010 named the accepted language and said the front matter gives `title` and `author`
and nothing else, and that comments are removed. 0020 then gave the front matter
`heading-1` … `heading-6`, and 0021 gave some comments and paragraphs a meaning: regions,
lists, captions. Each said what it added, but a reader of 0010 alone would not learn it.
The maintainer asked for the list to be restated in full here, so it stays one place.

## Decision

The dialect is CommonMark [S8], plus GFM tables, strikethrough and autolinks [S9], and
GitHub's footnotes [S10].

- **Blocks:** headings 1–6; paragraphs; code blocks; bullet and ordered lists, nested;
  tables, whose header row repeats on every page unless the build is told otherwise;
  blockquotes; thematic breaks; footnote definitions; task list items, as ☐/☑ with Segoe
  UI Symbol as the fallback font.
- **Inline:** emphasis, strong, strikethrough, code spans, links as real hyperlinks,
  footnote references, images.
- **Images:** PNG or JPEG from local files only, within the limits of 0011. Alt text goes
  to `descr`; the image is scaled to fit the page width.
- **Raw HTML:** only `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>`, and comments. Any other tag
  stops the build and names its line.
- **Comments** render nothing, except the region and list comments of 0021 —
  `<!-- front -->`, `<!-- chapters -->`, `<!-- back -->`, `<!-- appendices -->`,
  `<!-- toc -->`, `<!-- list-of-tables -->`, `<!-- list-of-figures -->` — each alone on its
  line at the top level. A comment that looks meant as one and is not taken warns with its
  line.
- **Captions:** a paragraph opening with `Table:` just before a table, or `Figure:` just
  after an image alone in its paragraph, is its caption (0021). One that is not in such a
  place stays text, with a warning.
- **Math** `$…$` and `$$…$$`: kept as literal LaTeX in code formatting, with a warning.
- **Front matter:** only flat `key: value` lines between `---` lines at the very top.
  `title` and `author` go to the document properties; `heading-1` … `heading-6` style the
  headings (0020), and a key that looks meant as one warns. Nothing else from it is used,
  and none of it enters the body.
- **Anything else** stops the build and names the line. Nothing is dropped silently.

Left out on purpose:

- Typeset math — it needs LaTeX converted to OMML in both languages; v0.2.
- SVG and remote images.
- General HTML — it would need a layout engine, and JavaScript has no standard HTML parser
  to match Python's byte for byte.
- Attribute syntax on blocks (`{…}`), and any construct that is not CommonMark or GFM
  text: the settings a document needs go in the front matter or in comments, which every
  other Markdown reader shows as nothing.

## Why

A converter that guesses silently is a converter that changes content (0023). The accepted
set covers what a Thai report, proposal or thesis uses, and footnotes are common in Thai
academic writing. Remote images are out because several runtimes have no network
[S12][S16]. The front matter and comments carry what the text cannot — heading looks,
the parts of a thesis — without a syntax that would print in other readers; where a
comment or a caption paragraph looks meant but is not taken, a warning keeps the promise
that nothing is lost unseen.

## Expires when

A construct outside the list is needed often enough to earn an implementation in both
languages — a new record per construct.
