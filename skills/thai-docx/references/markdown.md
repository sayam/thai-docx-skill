# Markdown: what the build reads

Read this before writing the Markdown for a document (SKILL.md, Build a document).

CommonMark, plus GitHub's tables, strikethrough, autolinks, task lists and
footnotes.

- **Blocks:** headings `#` to `######`; paragraphs; fenced or indented code; bullet
  and numbered lists, nested; tables (the header row repeats on every page unless `--no-repeat-table-header`);
  blockquotes; `---`; task items `- [ ]` and `- [x]`; footnotes `[^1]`.
- **Inline:** `*italic*`, `**bold**`, `~~strike~~`, `` `code` ``, links, footnote
  references, images.
- **Links** lead to `http`, `https` or `mailto`, in any case; a link with no scheme (`#top`,
  `other.docx`) is written as it is. Any other scheme (`javascript:`, `file:`, `ftp:`) stops the
  build with its line number. A link's target is written percent-encoded, as Word writes one; its
  text is unchanged. Parentheses nest in a link's destination 32 deep, as cmark reads them.
- **Bare addresses** become links as GitHub finds them: `www.…` and `http(s)://…`, a Thai
  domain too (`www.ตัวอย่าง.ไทย`); an email; `mailto:…`, the prefix included. `ftp://` and
  `xmpp:` stay text. A footnote's label matches in any case, as a link's does.
- **Numbered lists** start where the first number says, `0.` included.
- **Images:** local PNG or JPEG only, in the Markdown file's folder or below it. For
  an image elsewhere, add `--allow-dir <that folder>`. No remote images, no SVG.
- **HTML:** only `<br>`, `<sup>`, `<sub>`, `<u>`, `<kbd>`, and comments (removed), inside the
  text of a paragraph. Any other tag stops the build with its line number: rewrite it as Markdown.
  One of those five alone on its own line is an HTML block, and stops it too: write it on the
  line with the words around it.
- **Characters a reader cannot see** stop the build with their line: the zero-width five, a soft
  hyphen, a direction mark, any other format character, and noncharacters.
- **Math:** `$…$` and `$$…$$` stay literal LaTeX in code formatting, with a warning.
- **Front matter:** only flat `key: value` lines between `---` lines at the very top;
  `title` and `author` become the document properties, `heading-1` … `heading-6` style
  the headings ([heading-styles.md](heading-styles.md)), and other keys are ignored. Any
  other shape (lists, nesting) is read as ordinary Markdown text.

A line break inside a paragraph between two Thai characters joins them with no
space, so wrapping long Thai lines in the Markdown is safe.

What the build warns about rather than refuses: an image with nothing between the brackets
of `![]`, a heading level skipped, a link definition nobody refers to, **ำ written the long way
as `ํ` + `า`**, and a paragraph that opens with `ตาราง:` or `รูป:` where a caption would go — the prefix is `Table:` or `Figure:`,
in English, in every language. Entities (`&nbsp;`, `&amp;`) are resolved by CommonMark, so
`&nbsp;` becomes one non-breaking space in the document, not seven characters.

The text itself is never altered, only reported: `ํ` + `า` looks exactly like `ำ` and is left as
the two characters it is, because no Unicode normalisation joins them — NFKC takes `ำ` apart into
these two, never the other way. Replace them yourself if you meant `ำ`; a reader's search for `ำ`
will not find the long form.

Anything else stops the build and names the line, and so do blocks or formatting nested
more than 100 deep. Nothing is dropped silently.

**Where this reading and GitHub's differ, on purpose.** GitHub drops or bends these; the build
stops and names the line: a comment never closed, or text after a comment on its line; a table
row with more cells than its header — a `|` inside `` `code` `` in a table is written `\|`; a
footnote defined twice or never referenced; `<?…?>`, `<!DOCTYPE …>`, `<![CDATA[…]]>`. A
non-breaking space at the edge of a paragraph is kept, as CommonMark says. In a bare address
GitHub reads the source as written: an entity inside one is written as the character it stands
for, and `*` or `~` inside one may be read as formatting instead.
