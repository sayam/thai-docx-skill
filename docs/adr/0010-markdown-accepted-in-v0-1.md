# 0010 — What Markdown v0.1 accepts, and what stops the build

- Status: accepted
- Decided: 2026-09-15

## Where it came from

Once Markdown was the only input (0007), the accepted language had to be named,
along with what happens to everything outside it. Images, raw HTML, footnotes,
math and task lists were each costed for both implementations (0008) before
deciding.

## Decision

The dialect is CommonMark [S8], plus GFM tables, strikethrough and autolinks
[S9], and GitHub's footnotes [S10].

- **Blocks:** headings 1–6; paragraphs; code blocks; bullet and ordered lists,
  nested; tables, whose header row repeats on every page; blockquotes; thematic
  breaks; footnote definitions; task list items, as ☐/☑ with Segoe UI Symbol as
  the fallback font.
- **Inline:** emphasis, strong, strikethrough, code spans, links as real
  hyperlinks, footnote references, images.
- **Images:** PNG or JPEG from local files only, within the limits of 0011. Alt
  text goes to `descr`; the image is scaled to fit the page width.
- **Raw HTML:** only `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>`, and comments,
  which are removed. Any other tag stops the build and names its line.
- **Math** `$…$` and `$$…$$`: kept as literal LaTeX in code formatting, with a
  warning.
- **Front matter:** `title` and `author` go to the document properties. Nothing
  else from it is used, and none of it enters the body.
- **Anything else** stops the build and names the line. Nothing is dropped
  silently.

Left out on purpose:

- Typeset math — it needs LaTeX converted to OMML in both languages; v0.2.
- SVG and remote images.
- General HTML — it would need a layout engine, and JavaScript has no standard
  HTML parser to match Python's byte for byte.

## Why

A converter that guesses silently is a converter that changes content (0005).
The accepted set covers what a Thai report, proposal or thesis uses, and
footnotes are common in Thai academic writing. Remote images are out because
several runtimes have no network [S12][S16].

## Expires when

A construct outside the list is needed often enough to earn an implementation in
both languages — a new record per construct.
