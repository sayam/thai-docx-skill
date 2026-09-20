# 2026-09-20 — a section break inside a field is a section break Word may take away

A defect in the bytes this skill writes, found by reading the release-check files and confirmed in
the packages themselves. Not an application's limit, so
[ADR 0012](../adr/0012-xml-checks-are-the-proxy-office-apps-the-oracle.md)'s reference application
does not excuse it.

## What the files said

A section's properties live on its last paragraph. `_end_section` put them there without asking
what that paragraph was, and where a region ends in a list of contents, tables or figures the last
paragraph is **the field's own last entry**:

```xml
<w:p><w:pPr><w:pStyle w:val="TOC1"/><w:sectPr>…</w:sectPr></w:pPr>
  …last entry…<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>…สารบัญตาราง…</w:p>
```

Counted in the goldens of `main` 24a90a5, by walking each `document.xml` and tracking field depth:

| golden | section breaks | of them inside a field |
|---|---|---|
| `thesis-text` | 17 | **3** |
| `thesis-options` | 17 | **3** |
| `thesis-layout` | 17 | **3** |

The three are the same three every time: `TOC \o "1-3" \h \z \u`, `TOC \h \z \t "Table Caption,1"`
and `TOC \h \z \t "Figure Caption,1"`. `--toc` was never among them — that path has always written
`<w:p><w:pPr/></w:p>` after its field, and the break landed on that paragraph instead.

## What it does when a field is updated

Updating a field rewrites every paragraph between its `separate` and its `end`. A section break on
one of them is rewritten with it.

- **Word 365 for Windows, desktop** keeps the final paragraph mark when it updates, so the break
  survives and nothing shows.
- **Word for the web** replaces those paragraphs outright. The break goes, the pages reflow, and
  the heading that followed either vanishes or comes out below the content. The symptom needed a
  **second** update to appear; on one pass the document looked intact.

That difference is why this stood in six releases without being seen: the reference application is
the one that hides it.

## The fix

A section no longer closes in a paragraph a field holds. It closes in a paragraph of its own after
the list — the shape `--toc` already wrote:

```xml
  …last entry…<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
<w:p><w:pPr><w:sectPr>…</w:sectPr></w:pPr></w:p>
```

`_end_section` asks first (`_holds_a_field`): a paragraph carrying any part of a field, or one a
field opened before and has not closed, is not a paragraph to close a section in. Counted again
afterwards: **0 of 17** in every thesis golden, and `document.xml` grew by 78 bytes — 26 for each
of the three paragraphs, the break itself only moving.

The four thesis goldens are regenerated. `sample-default` and `sample-all-flags` are unchanged to
the byte, which is the other half of the measurement: no document without a list at the end of a
region is touched.

## Still owed

Word for the web's update is **not deterministic** — the same field bytes behaved differently
between `sample-options` and the `--thai-language` build on the same day — so one clean pass proves
nothing. Before v0.2.0 is tagged, the regenerated documents are opened there and their fields
updated **twice**, in both of those documents, and the section breaks are still in place.
