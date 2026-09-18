# Changelog

Notable changes to the thai-docx skill. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). A release is tagged only
when `metadata.version` in `SKILL.md`, the newest section here and the tag agree
(`python3 tools/package_skill.py --tag vX.Y.Z`), and after the checks of ADR 0012.

## [Unreleased]

### Added

- A release carries its own attestation. The build-provenance bundle is attached beside the archive
  as `thai-docx-<version>.intoto.jsonl`, so the proof travels with the file and a reader can check
  it offline, with no GitHub account: `gh attestation verify thai-docx-<version>.zip --bundle
  thai-docx-<version>.intoto.jsonl --repo sayam/thai-docx-skill`. The workflow now verifies both
  ways — against GitHub and against the file it is about to attach — and attaches nothing if a
  tampered archive passes either.

### Added

- `thai_docx repair IN.docx OUT.docx` — the repairs of v0.2 (ADR 0032). It clears findings `1`
  (compatibility mode 15), `2` (`<w:cs/>` and a Thai `w:lang` on every run with text), `3`
  (`<w:noProof/>` removed) and `5` (the complex-script twins, a `w:cs` font, a Thai-capable bullet
  font), writes a **new** file, reports `4`, `invisible` and `order` in `remaining`, and refuses to
  write at all if the text would differ by one character. New elements go where the schema puts
  them, so a repair never trades one finding for another.
- The font a run without one is given: `--font` if you name it, else the complex-script font the
  document already uses most — counting only fonts known to carry Thai — else this skill's default.
  The choice comes back in `warnings`.
- **A repaired file is larger.** The parts it rewrites are stored, not compressed, because both
  implementations must write the same bytes. A python-docx file of 36 KB comes back as 382 KB,
  almost all of it one 349 KB styles part that used to deflate to 12 KB. Opening it in Word and
  saving compresses it again. A deflate of this project's own is the next piece of work.
- A package can be written back as it came. `package.repack` (and `repackZip` in JavaScript) writes
  the entries in the order they had, copying the compressed bytes of every entry it was not asked to
  replace — method, checksum, sizes, date, "version made by" and attributes kept — and storing only
  the parts given anew. Every package in this repository, written back with nothing replaced, is
  byte for byte the file that went in. It is the first step of v0.2's repair (ADR 0032): the
  builder's packer stores every entry, which would hand a user's own document back about twenty
  times larger.

- The build names what it did not write, without refusing anything: an image with nothing between
  the brackets of `![]`, a heading level skipped, a link definition nobody refers to, and a
  paragraph opening with `ตาราง:` or `รูป:` where a caption would go. `grill` says when a message
  was read only to its 20,000-character cap, so an agent can tell that answer from a user who never
  asked for the interview. No document's bytes change.

### Fixed

- `check` says when it is the path that is wrong. A file that does not exist, or a directory,
  answered `findings: [{"code": "package", "message": "not a zip package"}]` — so a user who
  mistyped a name was sent looking for a damaged Word file. It now answers `error: cannot read …:
  No such file or directory`, with no findings, as `build` has always done. A file that opens and
  is not a zip is still a finding about the document.
- SKILL.md said documents with no Thai are not for this skill, while `build` builds them; it now
  says such a document needs nothing the skill adds, and to build one only if asked. Both
  troubleshooting pages said the trigger phrase needs a hyphen, which stopped being true when the
  space spelling was fixed earlier the same day.
- Every page that states a rule now points at the record in force. ADR 0025 and 0003 were
  superseded by 0030 and 0031 on 2026-09-18, and the assurance case, the architecture page,
  CONTRIBUTING, the roadmap, three gate titles, both implementations and the tests still cited
  them — including the message a user reads when an image lies outside the Markdown's tree. The
  section numbers were mapped, not substituted: 0011's §6 and §7 are 0030's §8 and §9. Evidence
  records and past changelog entries keep the names they were written with.
- `check` reads the comments. `word/comments.xml` was not among the parts it walked, so a Thai run
  with no complex-script marks inside a comment passed as clean. Word draws a comment beside the
  page and its spelling checker reads it, so it has the same fault as the body. Nothing this skill
  builds is affected — it writes no comments — but a file from another program can carry them.
- An image must be whole. A PNG whose pixels never arrived — a signature and an IHDR and nothing
  else, as a stopped copy or download leaves — was embedded and the build reported success. A PNG
  now has to end with its IEND chunk and a JPEG with its end-of-image marker, or the build refuses
  with exit 2.
- An image too large to carry is the user's input, not a defect in this skill. A valid photograph
  that pushed the package past the size a .docx may be here left `build` through the `findings`
  path, which SKILL.md reads as "a defect in this skill; do not retry" — so a user with a scan in
  their thesis was sent to the issue tracker. It is now an `error` with exit 2, which is the door
  for input a user can change, and matches what `check` already did for the same finding.
- `grill` reads one message one way. The JavaScript counted the 20,000-character cap in UTF-16
  units, so a message with 10,000 emoji and the phrase `thai-docx grill` started the interview in
  Python and skipped it in JavaScript; it now counts characters, as ADR 0029 says and ADR 0008
  requires. And the phrase is read with a space between the two words of the name
  (`thai docx grill`), which ADR 0026 has always allowed and the code never did.

### Changed

- What the agent reads says what the code does: SKILL.md counts comments among the HTML the build
  takes, `references/profiles.md` gives each profile command's JSON line and the 64 KiB a profile
  file may reach, and the settings reference says `--no-page-number-first` is about the first page
  of each section, not only page 1.

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
