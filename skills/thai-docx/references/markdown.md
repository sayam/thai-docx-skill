# Markdown: what the build reads

Read this before writing the Markdown for a document (SKILL.md, Build a document).

CommonMark, plus GitHub's tables, strikethrough, autolinks, task lists and
footnotes.

- **Blocks:** headings `#` to `######`; paragraphs; fenced or indented code; bullet
  and numbered lists, nested; tables (the header row repeats on every page unless `--no-repeat-table-header`);
  blockquotes; `---`; task items `- [ ]` and `- [x]`; footnotes `[^1]`.
- **Inline:** `*italic*`, `**bold**`, `~~strike~~`, `` `code` ``, links, footnote
  references, images.
- **Images:** local PNG or JPEG only, in the Markdown file's folder or below it. For
  an image elsewhere, add `--allow-dir <that folder>`. No remote images, no SVG.
- **HTML:** only `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>`, and comments (removed).
  Any other tag stops the build with its line number: rewrite it as Markdown.
- **Math:** `$…$` and `$$…$$` stay literal LaTeX in code formatting, with a warning.
- **Front matter:** only flat `key: value` lines between `---` lines at the very top;
  `title` and `author` become the document properties, `heading-1` … `heading-6` style
  the headings ([heading-styles.md](heading-styles.md)), and other keys are ignored. Any
  other shape (lists, nesting) is read as ordinary Markdown text.

A line break inside a paragraph between two Thai characters joins them with no
space, so wrapping long Thai lines in the Markdown is safe.

What the build warns about rather than refuses: an image with nothing between the brackets
of `![]`, a heading level skipped, a link definition nobody refers to, and a paragraph that
opens with `ตาราง:` or `รูป:` where a caption would go — the prefix is `Table:` or `Figure:`,
in English, in every language. Entities (`&nbsp;`, `&amp;`) are resolved by CommonMark, so
`&nbsp;` becomes one non-breaking space in the document, not seven characters.

Anything else stops the build and names the line, and so do blocks or formatting nested
more than 100 deep. Nothing is dropped silently.
