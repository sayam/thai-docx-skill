# An example, not a standard

`thesis.md` and the profile beside it (`../profiles/thesis.json`) are one worked example of the
most a document can ask this skill for. They are there to be copied and changed.

**They are not a template anyone must follow.** This skill does not decide what a thesis, a
report or an official letter should look like; no university's or ministry's format is
reproduced here, and every word and number in the example is invented. What a document looks
like is the writer's to choose, and every part of the example is a setting you can change or
leave out.

## Build it

```sh
python3 <skill>/scripts/thai_docx build <skill>/examples/thesis.md thesis.docx --profile thesis
```

The profile is found by name because it is shipped with the skill; a profile of your own with
the same name, in the project or in your home directory, wins over it.

## What is where, and why

A document's shape comes from two places, and the difference is worth knowing before you change
anything.

**The profile — settings you reuse across documents.** `--profile thesis` carries Thai
distributed alignment, a first-line indent, 1.5 line spacing, page numbers at the top right with
none on the first page of a section, numbered sub-headings, Thai digits, and the chapter title on
its own line. This is what answering the interview (`thai-docx grill`) leaves behind: run it,
answer as you like, and save the answers under a name of your own.

```sh
python3 <skill>/scripts/thai_docx profile save my-thesis --from thesis --default thai_digits
```

That takes the example as a starting point and turns one setting off. `profile show my-thesis`
prints what it holds.

**The Markdown — this document's own shape.** The region comments (`<!-- front -->`,
`<!-- chapters -->`, `<!-- back -->`, `<!-- appendices -->`), the `Table:` and `Figure:` captions,
the three list comments, and the `heading-1` … `heading-3` lines in the front matter belong to the
file, not to the profile. The heading lines are what make a heading 20 pt, centred and on a new
page; copy the block into your own file and change the numbers.

## What it costs, said here rather than found later

This example uses `--thai-digits`, and it has region comments. Either of those means **the
numbers in the finished .docx do not renumber themselves**: a reader who opens it in Word and
inserts a chapter or a table renumbers from there by hand. The contents, the list of tables, the
list of figures and the page numbers still update.

The reason is in `../references/chapters.md`: no application but Word works out a chapter-numbered
caption correctly, and LibreOffice draws Thai digits as 1, 2, 3. The way back is the one the skill
is built for — change the Markdown and build again, where every number is worked out afresh.

A report with no region comments and no Thai digits keeps Word's own numbering and renumbers
itself as before.

## The files

| | |
|---|---|
| `thesis.md` | the example document — cover, front matter, chapters, appendices, back matter |
| `figure.png` | a placeholder image, so the figure caption has something to sit under; replace it |
| `../profiles/thesis.json` | the settings, as an interview would leave them |
