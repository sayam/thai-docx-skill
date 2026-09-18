# 2026-09-18 — a comment is text the reader sees

The third item of the triage from the adversarial reviews of 2026-09-18. Cursor's Grok 4.6 noticed
that `check` walks a fixed list of parts and that `word/comments.xml` is not on it.

## What was wrong

`check.py:50` and its JavaScript twin:

```python
TEXT_PARTS = re.compile(r"word/(document|footnotes|endnotes|header[0-9]*|footer[0-9]*)\.xml")
```

Everything a reader sees was there except the comments. Re-run here before it was believed: a
golden with a comment added, whose run carries no marks at all —

```
$ python3 … check withcomment.docx
{"ok": true, "counts": {"runs": 66, "paragraphs": 41, "tables": 1, "footnotes": 1}, "findings": []}
rc = 0
```

`ok: true` over a file with an unmarked Thai run in it. Word draws a comment beside the page, its
spelling checker reads it, and its line breaking applies to it — so a comment has exactly the
problem ADR 0004 is about, and the checker said the file was clean.

The reach is small but real: this skill never writes comments, so no file it built is affected. It
matters for the files `check` exists for — the ones another program wrote, or a person edited in
Word, where comments are where review happens.

## What changed

`comments` joins the pattern in both implementations. Nothing else moves: the same run rules, the
same finding codes, the same part name in the finding.

`references/check.md` now says which parts the check reads — body, comments, footnotes and endnotes,
headers and footers — and tells the agent to name the part when a finding is not in the body,
because "there is a problem in your document" is not useful when the problem is in a comment.

## Tests, red before the change

`tests/test_check.py::test_a_comment_is_text_the_reader_sees`:

- a comment whose run has an empty `rPr` gives exactly one finding, code `2`, with
  `part == "word/comments.xml"`;
- the same comment with the marks is clean, and its paragraph is counted — one more than the same
  package without the comment, which shows the part is really being walked and not merely skipped
  more quietly.

227 tests pass; ruff and ESLint are clean; the bundle was regenerated.

## What is still not read

`word/commentsExtended.xml`, `word/commentsIds.xml` and `word/people.xml` travel with comments in
files Word writes. They carry ids, dates and author names, not document text, so there is nothing
for ADR 0004's rules to find in them. `word/glossary/document.xml` — the building blocks of a
template — does hold text and is still not read; no file this project has met carries one, and a
part that is not walked is better named here than assumed to be covered.
