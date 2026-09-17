# Changelog

Notable changes to the thai-docx skill. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). A release is tagged only
when `metadata.version` in `SKILL.md`, the newest section here and the tag agree
(`python3 tools/package_skill.py --tag vX.Y.Z`), and after the checks of ADR 0012.

## [Unreleased]

## [0.1.1] - 2026-09-18

The documents the skill builds are byte for byte those of 0.1.0 (the goldens are unchanged), so the
checks of ADR 0012 in the office applications carry over.

### Changed

- SKILL.md and `references/chapters.md`: the optional thesis flags are named only by the words a
  user says for them, and a message that begins with the skill's name keeps those words when it is
  passed to the grill command.
- `profile save` reports `"replaced"`, as `profile import` already did: true when a profile of
  that name was there and the save took its place. Both then also carry a warning saying so. The
  guides warn that `build`, `profile save` and `profile import` replace without asking.
- The skill's description is 195 characters (was 731), so the skill uploads in the Claude
  apps, which take 200, and ends with the repository's address.
- Every source file of the skill opens with SPDX copyright and licence lines; the two files ported
  from commonmark.js name BSD-2-Clause and its author too.

### Fixed

- Reading a profile stops one byte past its 64 KiB limit instead of asking the file's size first,
  in both implementations. A file that grew between the two, or has no size at all (`/dev/zero`),
  made the command read without end; it is now refused as larger than 64 KiB.

## [0.1.0] - 2026-09-17

The first version. Checked in Word 365 for Windows (desktop and web), Word for macOS, Google
Docs, LibreOffice Writer and WPS Writer (ADR 0012; `docs/evidence/2026-09-16-office-check-five-applications.md`,
`docs/evidence/2026-09-17-word-for-macos.md`).

### Added

- `thai_docx build IN.md OUT.docx`: Markdown (CommonMark with GitHub's tables,
  strikethrough, autolinks, task lists and footnotes) to a .docx that avoids the five
  causes of broken Thai in Word (ADR 0004). The build refuses to write a package that
  fails its own checker or differs from the Markdown by one character (ADR 0023).
- `thai_docx check FILE.docx`: reports each of the five causes, invisible characters
  and unreadable or unsafe packages, for a .docx from any generator (ADR 0006, 0017).
- Two implementations with byte-identical output: Python 3.11+ with the standard
  library only, and one JavaScript file for Node.js or a sandbox (ADR 0008).
- Default settings announced after every build; grill mode asks nine fixed questions,
  each with fixed choices, first (ADR 0026, restating 0019).
- `thai_docx grill --said "MESSAGE"`: the script, not the agent, says which mode a request
  is in — the interview starts only when the user's own message holds `thai-docx grill`
  (ADR 0026).
- `--indent IN`: a first-line indent for body paragraphs, none by default (ADR 0026).
- `--page-numbers [top-right|top-center|bottom-center]`: where the page number goes;
  top right when no position is given.
- Profiles (ADR 0024): `--profile NAME|PATH` for a build, and `thai_docx profile
  list | show | save | export | import`. A profile is a JSON file of settings, checked as
  the flags are, found in the project, the user's home or the skill; `export` writes the
  file to hand to someone, `import` takes theirs. Grill mode's ninth question keeps the
  answers as one. The script limits are restated for it (ADR 0025, superseding 0011).
- Reports and theses (ADR 0021): `<!-- front -->`, `<!-- chapters -->`, `<!-- back -->`
  make a next-page section of the cover, every `#` and each region, front pages counted
  ก ข ค and chapters from 1; chapter headings read "บทที่ 1"; `Table:` and `Figure:`
  paragraphs become captions numbered by chapter ("ตารางที่ 1-1"); `<!-- toc -->`,
  `<!-- list-of-tables -->` and `<!-- list-of-figures -->` place the lists;
  `--chapter-label`, `--table-label`, `--figure-label` change the words;
  `<!-- appendices -->` letters its headings "ภาคผนวก ก" and captions "ตารางที่ ก-1";
  `--front-page-numbers` and `--appendix-numbers` choose the number styles.
- Lists carry their entries (ADR 0027): a table of contents, tables or figures written by
  the build already holds its lines, so Word on the web, Google Docs, LibreOffice Writer and
  WPS Writer show them without a field update; page numbers still need one. Every numbering
  level, the `Hyperlink` style and `Normal` name the document's font, size and complex-script
  flag, so an application that does not read `w:docDefaults` still draws Thai correctly.
- `--chapter-title-on-new-line`: "บทที่ 1" keeps its own line and the chapter's title starts
  the next, in the chapters and the appendices; the lists still read one line.
- Heading styles in the front matter: `heading-1` … `heading-6` take CSS-like declarations —
  font, size, colour, weight, style, underline, alignment, indents, spacing, page break
  (ADR 0020).
- `--heading-numbers`: headings numbered by Word from `#` down (1., 1.1, 1.1.1), in Thai
  digits with `--thai-digits`; the heading text is not changed.
- `--header TEXT` and `--footer TEXT`: a line of text centred at the top or bottom of every
  page, above the page number when it shares the place; kept on a first page without
  its number.
- `--no-page-number-first`: with `--page-numbers`, the first page (a cover, or the first
  page of a letter) has no number; the second page shows 2.
- `--paper f14`: 8.5 × 13 in (folio) paper, beside A4 and Letter.
- `--landscape`: the paper turned sideways; margins keep their sides, and tables and
  images take the wider text width.
- `--thai-digits`: page numbers, the table of contents' page numbers, numbered lists and
  footnote marks in Thai digits (๑ ๒ ๓); digits in the text are never changed.
- `--line-spacing N`: line spacing from 1 to 3 times single, single by default; code blocks
  and footnotes stay single.
- `--table-size PT`: the size of the text in table cells, the body size by default.
- `--table-widths auto`: table columns sized by the longest text each holds, every column
  at least a quarter of an equal share; `equal` stays the default.
- `--no-repeat-table-header`: a table's header row appears once instead of at the top
  of every page it runs onto; by default it repeats (ADR 0022).
- A release archive holding only the skill directory; the gates travel with forks and
  hold every pull request at merge (ADR 0018).
- Grill from a profile and save as another (ADR 0029): `thai-docx grill from thesis save to
  thesis-v1` (or `จาก`, `บันทึกเป็น`; `only`/`เฉพาะ` to ask some questions) starts the
  interview from a profile's answers; the grill command gives the questions, the choice each
  setting holds now, and the flags each choice means. `--default SETTING` gives a setting
  of a profile back to its default, on `build --profile` and `profile save --from`.
- A flag that changed nothing is said out loud (ADR 0028): the build warns when a table,
  caption, region or thesis flag has nothing in the document to act on — exactly when the
  file is the same with the flag as without — and when `--toc` would add a second table of
  contents beside `<!-- toc -->`.
- `references/settings.md`: every setting, its default and an example flag, generated from
  the settings registry.
- Step-by-step user guides for thirteen scenarios, from a plain request to editing a saved
  profile, in Thai and English (`docs/guide/`, linked from the README).
- The number Word draws for a heading — "บทที่ 1", "1.1", "ภาคผนวก ก" — takes its heading's
  size, font, weight and colour, including what the front matter's `heading-n` sets.
- `--align thai` spreads Thai lines only: a paragraph with no Thai stays left-aligned, and the
  line before a hard break is not spread letter by letter.
