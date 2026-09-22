# Changelog

Notable changes to the thai-docx skill. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). A release is tagged only
when `metadata.version` in `SKILL.md`, the newest section here and the tag agree
(`python3 tools/package_skill.py --tag vX.Y.Z`), and after the checks of ADR 0012.

## [Unreleased]

### Added

- **The rules this project decides by, written down** (`docs/rules.md`): the scope the skill
  answers for, what an output must be, what it must never introduce, the contract the five office
  applications are held to, and the limitations that must be said out loud. The Thai is the rule,
  in the maintainer's own words; the English below it is a translation marked as one. Its last
  table is the trace — which decision record applied each rule, and what was seen. GOVERNANCE.md
  carries the rules at its head and `docs/architecture.md` says the design is one way of meeting
  them; neither repeats them, because two copies of a deciding text drift.
- **A gate on the project's own citations** (`live-pages-cite-the-record-in-force`): no page that
  states a rule now may point at a record the index marks superseded, unless it names the record in
  force on the same line. Twenty-three files were doing so when it was written — among them two
  messages a user reads, which named ADR 0005 where 0023 has held since 2026-09-16 — and each was
  mapped to the record in force, section numbers included. The check is the one ROADMAP.md had been
  carrying since the drift of 2026-09-18 was found by a reviewer rather than a gate.

- **Two limits of the applications, written where a user meets them** (`references/limits.md` §3
  and §7, and both guides' troubleshooting tables). **Google Docs must never be asked to update
  the lists**: it has no list of tables and no list of figures of its own, so an update rewrites
  all three as a contents built from headings and the two lose their entries — the entries are
  already in the file, so they are read there as they came, and the way back from an update is to
  download the document again. **Word for the web has no TH Sarabun New** in its font list, only
  TH SarabunPSK; asked for a font it does not have it substitutes one whose mark metrics are not
  the font's, and the tone marks float above the letter throughout the document, text typed in by
  hand included. A document to be read or edited there is built with `--font "TH SarabunPSK"`.
  Neither is reachable by anything the file could say differently, and the default font is
  unchanged.
- A release carries its own attestation. The build-provenance bundle is attached beside the archive
  as `thai-docx-<version>.intoto.jsonl`, so the proof travels with the file and a reader can check
  it offline, with no GitHub account: `gh attestation verify thai-docx-<version>.zip --bundle
  thai-docx-<version>.intoto.jsonl --repo sayam/thai-docx-skill`. The workflow now verifies both
  ways — against GitHub and against the file it is about to attach — and attaches nothing if a
  tampered archive passes either.


- **`--auto-numbering`: the application counts, and Word renumbers as the reader edits** (ADR
  0036). Headings take a multilevel list tied to the heading styles, ordered lists a numbering
  level, and a caption the pair of fields Word's own Insert Caption writes — `STYLEREF 1 \s` and
  a `SEQ` that starts again at each chapter — in `thaiNumbers` and `\* ThaiArabic` with
  `--thai-digits`. Every field's result is still written in. It is for a document someone will go
  on working on in Microsoft Word; what LibreOffice Writer, WPS Writer, Google Docs and Word for
  macOS draw with it is in the new `references/numbering.md`, measured or marked not measured.
  The flag says it changed nothing in a document with nothing to count. The release oracle gains
  a variant, `sample-auto`, whose checklist asks that an inserted heading, list item and caption
  renumber what follows; the reference application must pass it.
- WPS Writer re-checked (11.1.0.11723): both fixes of 0.1.0 hold there, the three lists fill on
  open, and what WPS draws its own way is recorded — including a new one, the numbering value 1
  drawn as ๕ under `--thai-digits`. The check also found that the task-list boxes `☐` and `☑` are
  written in Segoe UI Symbol, which no Linux machine has, so they draw as nothing outside Windows.
- The two installers are held by tests, not only by a promise. The archive and the subtree
  `skills/thai-docx/` that `gh skill install` and `npx skills add` copy must be the same files
  **and the same bytes**; and the front matter must survive being written again the way
  `gh skill install` writes it — keys sorted, `metadata` flattened, quotes dropped — so nothing
  depends on their order, `version` keeps its two dots, and no key inside `metadata` shares a name
  with a top-level one. Both guides now say which installer gives the release and which gives
  `main`, with `--pin` and `gh skill preview`.
- `thai_docx repair IN.docx OUT.docx` — the repairs of v0.2 (ADR 0032). It clears findings `1`
  (compatibility mode 15), `2` (`<w:cs/>` and a Thai `w:lang` on every run with text), `3`
  (`<w:noProof/>` removed), `5` (the complex-script twins, a `w:cs` font, a Thai-capable bullet
  font) and `order` (a run's, a paragraph's and the settings' properties put back in the order the
  schema fixes, with anything the schema does not name left where it is). It writes a **new** file,
  reports `4` and `invisible` in `remaining` — repairing either would change the user's text — and
  refuses to write at all if the text would differ by one character. New elements go where the schema puts
  them, so a repair never trades one finding for another.
- The font a run without one is given: `--font` if you name it, else the complex-script font the
  document already uses most — counting only fonts known to carry Thai — else this skill's default.
  The choice comes back in `warnings`.
- A deflate of this project's own, so a repaired file is about the size it was. The parts a repair
  rewrites could not be compressed by a library — no two promise the same bytes, and ADR 0008 says
  both implementations must agree — so they were stored, and a python-docx file of 36,810 bytes came
  back as 381,937. `deflate` fixes every choice a compressor is free to make, in both
  implementations, and that file now comes back as 39,437. It reaches 4.1% on the styles part that
  caused the growth, against zlib's 3.5%.
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

- `ำ` typed the long way is named, and left exactly as it was. `ำ` (U+0E33) can also be written as
  `ํ` + `า` (U+0E4D U+0E32); the two look the same on screen and are not the same text in the file, so a
  reader's search for `ำ` skips the long form. The build now warns, with the line number, and changes
  nothing: U+0E33's decomposition is `<compat> 0E4D 0E32`, so NFKC turns `ำ` **into** the pair and no
  normalisation turns the pair back — joining them would be a transformation this project invented
  (ADR 0034, ADR 0023), and the form NFKC would leave everywhere is the one WPS already misplaces.
  `&nbsp;` keeps CommonMark's reading, which `references/markdown.md` states, and gets no warning.
  No document's bytes change.

- `references/specs.md` — everything the Markdown can say, in one page, for an assistant writing
  a document of a shape the user asked for. It was four files and an inference before: what the
  parser accepts, how a long document is marked up, what the front matter styles, what the flags
  set, what stops the build and what only warns. SKILL.md sends the agent there when a user shows
  an example of their own. **It describes a format, not a house style** — the skill carries no
  ministry's, university's or company's form, and the page says so in its own second paragraph;
  the assistant follows the user's example, not one of ours. The page's single example uses every
  construct at once and a test builds it, so the page cannot drift from the parser. Scenario 14
  of both guides walks the flow: show the example, read the specs, see the Markdown, then build.

- The skill ships one profile, `thesis`, and the document it belongs to. The profile loader has
  looked in the skill's own directory since ADR 0024 and found nothing there; a user who
  installed the skill saw rules about บทที่ and ตารางที่ and no example, which reads as a format
  the skill imposes rather than one it offers. `examples/README.md` says in its first line that
  it is an example and not a standard, which parts of a document a profile holds and which
  belong to the Markdown, and what it costs — a document with regions or Thai digits does not
  renumber itself. Every name in the example is invented; no real institution's format is
  reproduced.

### Changed

- **The build writes every number itself, in every document, unless `--auto-numbering` asks the
  application to count — one answer for the whole document (ADR 0036, which restates 0035).** A
  heading's number (`บทที่ ๑`, `๑.๑`, `ภาคผนวก ก`, `1.`), an ordered list's marker and a caption's
  number are runs in the paragraph they belong to, in Arabic digits or Thai, so the file reads the
  same in all five applications. The reason was measured: LibreOffice Writer drew a thesis's
  captions as `ตารางที่ บทนำ-ก` — the chapter's *title* where Word gives its number, from a
  `STYLEREF`, and a Thai letter that never restarted, from a `SEQ` — and drew `บทที่ 1`, `1.1`,
  `1.` where Word drew Thai digits, because `thaiNumbers` is a format it does not implement
  (26.8; `ก ข ค`, `A`, `I`, `i` and `1` are all right). **The cost is said where the user meets
  it: written numbers do not renumber themselves.** A reader who inserts a chapter in the .docx
  renumbers by hand from there, or changes the Markdown and builds again. Half-and-half is the one
  thing not on offer — a document that renumbers its headings but not its captions puts
  `ตารางที่ 1-1` in chapter 2 and says nothing. What only a laid-out page knows stays a field:
  page numbers, footnote marks, and the page numbers a list shows after an update. A bullet stays
  a numbering level, since `•` is written out and every reader drew it. **The three lists stay
  `TOC` fields**, which is what an application, and a person who edits the file afterwards, knows
  how to update — but a caption now takes a paragraph style of its own, `Table Caption` or
  `Figure Caption`, and the list collects that style with `\t` instead of a caption's `SEQ`
  fields, so it holds whoever counts. **The bytes of every document change**; the goldens were
  regenerated.
- The table of contents now carries sub-heading numbers too (`1.1 ที่มา`), because the build
  writes them and so knows them; before, an application that never updated fields showed the
  heading's words alone.
- `--chapter-label` and `--appendix-label` say they changed nothing unless a heading actually
  carries a chapter number or an appendix letter, which is what they always meant.
- The task-list box is now `□` and, when checked, `■`, in Arial (ADR 0033). It was `☐`/`☑` in Segoe
  UI Symbol — a Microsoft font, so on every machine without it the box was drawn as **nothing**, in
  every reader, which the WPS re-check found. No font carrying `☐` is present on Windows, macOS and
  Linux alike, so the characters had to change rather than the font name alone. **The bytes of a
  document with a task list change**, and the goldens were regenerated.


- What the agent reads says what the code does: SKILL.md counts comments among the HTML the build
  takes, `references/profiles.md` gives each profile command's JSON line and the 64 KiB a profile
  file may reach, and the settings reference says `--no-page-number-first` is about the first page
  of each section, not only page 1.

### Fixed

- **A caption the reader adds now joins the list of tables or figures**, where
  `--auto-numbering` asked the application to count. The lists collected their entries by the
  caption's *style*, which is the only thing to collect when a number is text — but a caption
  added with References → Insert Caption carries Word's own `Caption` style, and one pasted from
  another caption did not join the list either, however many times the fields were updated. Both
  numbered themselves correctly the whole time, because every caption carries a `SEQ` field named
  after its label. So under that flag the lists now collect **the counter** instead of the style,
  and gain every caption that carries it, whichever way the reader added it. Without the flag
  nothing changes: there are no `SEQ` fields to collect. Measured in Word 365 for Windows on
  2026-09-23; `thesis-auto` is the only golden that moves.

- **`repair` marks a run where its text is complex script, and cuts a run that holds both.**
  It used to mark every run that held text, the same defect the build had, so a repaired
  document underlined English exactly as a built one did. It now takes the marker off a run
  whose text is not complex script — and off the document defaults and the styles, without which
  a run that leaves it off only inherits it again — and cuts a run that holds both scripts where
  the script changes. Measured on the thesis fixture, attributes alone would have reached about a
  third of the English: 462 Latin letters sit in runs that are Latin only against 924 inside runs
  that hold Thai as well. It carries `--force-cs-whole-doc` too, with the same meaning as the
  build's. A run carrying a field, a picture, a tab, a break or a numeric character reference is
  never cut, because it could not be written again without touching the text, and
  `references/limits.md` §10 says so beside the rest of the repair contract.

- **Correctly spelled English words are no longer underlined.** Every run this skill wrote said it
  was complex script, including a run holding nothing but Latin letters, so Word proofed English
  with a complex-script language — and no complex-script language spells English. A run now says
  it where its text says it: runs are cut at the boundary between complex script and not, the
  marker goes on the complex-script ones and is left off the others, and neither `docDefaults` nor
  the `Normal` style carries it any more, so leaving it off means off. No run repeats the Latin
  language that `docDefaults` already declares; `--thai-language` still names the complex-script
  language, now on the marked runs only. Digits and ASCII punctuation are not complex script, and
  a space takes the script before it, both as Word writes them (ADR 0039).
  **Every document's bytes change** — `word/document.xml` of the thesis fixture is 4.96 per cent
  smaller — and **code spans now render in the font the document has always named for them**,
  which is Consolas rather than the body font. `--force-cs-whole-doc` writes the marker on every
  run instead, the shape releases before this one wrote, for a finished document meant to be read
  with one font throughout.

- **A section break no longer sits inside a table of contents, tables or figures.** A section's
  properties live on its last paragraph, and where a region ended in one of the three lists that
  paragraph was the field's own last entry. Updating a field rewrites every paragraph it holds, so
  the break was rewritten with them: Word 365 on the desktop keeps the final paragraph mark and
  never showed it, while **Word for the web** dropped the break, reflowed the pages and lost the
  heading that followed — on the *second* update, not the first. Three of the seventeen breaks in
  every thesis document were in this position. A section that ends in a list now closes in a
  paragraph of its own after it, which is the shape `--toc` has always written.
  **The bytes of a document whose region ends in a list change** (the four thesis goldens were
  regenerated, 78 bytes each); `sample-default` and `sample-all-flags` are unchanged to the byte.
- An English heading is aligned like its Thai twin. Under `--align thai`, a paragraph with no Thai
  in it is given `left` so English does not come out spread across the page — and a heading is a
  paragraph, so `# Abstract` was given it too, overriding the `text-align: center` its own style
  carried from `heading-1`. Beside it, `# บทคัดย่อ` was centred. A paragraph whose **style** fixes
  an alignment now keeps it (Heading1–6 and CodeBlock). Found in WPS Writer, true of every reader,
  since a paragraph property beats a style property. **The bytes of a document built with
  `--align thai` change** — they get smaller — and those two goldens were regenerated.
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
