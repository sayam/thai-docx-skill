# Changelog

Notable changes to the thai-docx skill. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). A release is tagged only
when `metadata.version` in `SKILL.md`, the newest section here and the tag agree
(`python3 tools/package_skill.py --tag vX.Y.Z`, which also refuses a tag whose goldens no reading
record names), and after the checks of ADR 0012. 0.2.0 was tagged
before two applications were read; the exception and what is owed are in
[its record](docs/evidence/2026-09-24-what-v0.2.0-was-read-in.md). The rule is unchanged.

## [Unreleased]

## [0.3.0] - 2026-09-26

**The goldens move**: most Thai documents are written differently from 0.2.2 — punctuation
between Thai, scripts besides Thai, a captioned table, a picture with `--indent` or in a list or a
quotation. What the five applications draw is read on these bytes before the tag.

### Added

- `check` says which way a document's numbers are made — `numbering`: `automatic`, `written`,
  `mixed` or `none`, with how many headings, captions and list items of each — the first step of
  ADR 0037, which lets the assistant ask which the document should be before anything renumbers
  it (`tests/test_what_a_command_takes.py::test_check_reads_which_way_the_numbers_are_made`).

### Changed

- The goldens may change bytes on `main` between releases. The rule that a reading record names
  every golden's sha256 is held where it matters, at the tag: `tools/package_skill.py --tag`,
  which the release workflow runs, refuses a tag until the newest record does
  (`tests/test_rules.py::test_the_newest_release_record_names_the_bytes_it_read`).
- The limits record what LibreOffice Writer, Google Docs and Word for the web draw their own way,
  read on 2026-09-26: page numbers and footnote numbers in Arabic digits where Thai ones were set,
  Thai distributed alignment drawn left in LibreOffice, a table of contents numbered from the cover
  and Thai proofed as Arabic in Word for the web, and what Word for the web does with
  `--auto-numbering`.

### Fixed

- A Thai mark with no letter before it (`นำ้`) and a letter with two tone marks went through in
  silence; each is named with its line and left as typed. The Markdown page says the text is read
  in NFC, which puts marks typed out of order on one letter in order
  (`tests/test_what_a_command_takes.py::test_a_thai_mark_out_of_place_is_named`).
- Every ASCII mark was a Latin run of its own, so `พ.ศ.` was four runs and `๑.๑` three.
  Punctuation with Thai on both sides is Thai now; between Thai and English it goes with the
  English, as Word puts the comma. **This changes the bytes of most Thai documents**, the goldens
  among them (`tests/test_what_a_command_takes.py::test_punctuation_between_thai_is_not_cut_out_of_it`).
- "Complex script" meant the Thai block, so a Lao, Khmer, Arabic or Devanagari run in a Thai
  document was written, checked and repaired as Latin. One list of the complex scripts marks,
  checks and repairs them all; finding `2` says "complex script" again
  (`tests/test_what_a_command_takes.py::test_every_complex_script_is_marked_checked_and_repaired`).
- A table with a `Table:` caption had no name for a screen reader or Word's accessibility check;
  the caption is written as its `w:tblCaption` too, which moves the bytes of every document with a
  captioned table. `--toc` in a document with no heading says its table of contents is empty
  (`tests/test_what_a_command_takes.py::test_a_captioned_table_is_named_and_an_empty_toc_is_said`).
- A picture was fitted to the text width and then indented, so with `--indent`, in a list or in a
  quotation it ran past the right margin by the indent. A picture alone in its paragraph takes no
  first-line indent now, and one that opens a paragraph or sits in a list or a quotation is drawn
  no wider than its line — which moves the bytes of a document with `--indent` and a picture
  (`tests/test_build_writes_what_it_was_given.py::test_a_picture_fits_the_line_its_paragraph_leaves_it`).

## [0.2.2] - 2026-09-26

**The goldens do not move**: a document is written as 0.2.1 wrote it unless it holds one of the
cases fixed below — a picture that leaves its caption less than an inch under
`--caption-matches-object`, a bare address GitHub reads as a link and 0.2.1 did not (or the other
way), a footnote whose label is written in two cases. `check` reads more of a file someone else
wrote, so it can find what it answered `ok` on before; `repair` puts right what it now finds.

### Changed

- **SKILL.md** names the page-number positions and heading numbers, and says to read the settings
  reference before using any other flag; says the grill message goes untranslated, and what to do
  when the answer says it was read only in part; and that a missing picture is the user's to
  give, never made up or deleted. Measured on three models: eighteen files of eighteen exact, no
  flag invented; one grill message of eighteen still paraphrased, through the Skill tool's
  argument ([record](docs/evidence/2026-09-26-model-equivalence-on-the-0.2.2-skill-md.md)).

### Fixed

- `check` read a Strict Open XML package as an empty document and answered `ok`; it is refused
  (`tests/test_check_reads_the_whole_package.py::test_a_strict_package_is_refused_not_read_as_empty`).
- `check` and `repair` read a switch that says off as on: `<w:cs w:val="0"/>` passed as marked,
  and `<w:noProof w:val="0"/>` was finding `3`
  (`tests/test_check_reads_the_whole_package.py::test_an_off_switch_is_read_as_off`).
- A part was known by its file name: a header named `headerFirst.xml` went unread, and a main
  document under another name was refused. Parts are found by the package's relationships
  (`tests/test_check_reads_the_whole_package.py::test_a_part_is_found_by_its_relationship_not_its_name`).
- A numbering level's and a paragraph mark's properties were never asked for their twins, and
  `repair` never gave them
  (`tests/test_check_reads_the_whole_package.py::test_a_numbering_level_has_its_twins_checked`,
  `tests/test_check_reads_the_whole_package.py::test_a_paragraph_marks_properties_are_checked`).
- The formatting a tracked change says a style once had was a finding
  (`tests/test_check_reads_the_whole_package.py::test_formatting_a_revision_replaced_is_not_a_finding`).
- Thai only in deleted text was not read, so its run passed unmarked
  (`tests/test_check_reads_the_whole_package.py::test_deleted_text_is_text`).
- `order` was checked in a run's, a paragraph's and the settings' properties only; a section's, a
  table's, a row's, a cell's, a paragraph mark's, a numbering level's and a style's are checked
  and repaired too
  (`tests/test_check_reads_the_whole_package.py::test_the_order_of_every_property_list_is_checked`).
- Every run wrote sixteen `.pyc` files into the installed skill's folder; now one, the entry
  point's, which Python writes before the skill runs, and none under `python3 -B`
  (`tests/test_script_limits.py::test_running_the_package_leaves_no_cache`).
- `profile export PATH` made every missing folder above `PATH`; it writes where it is told, or not
  at all (`tests/test_what_a_command_takes.py::test_profile_export_writes_where_it_is_told_and_makes_no_folder`).
- An encrypted entry that was not XML passed the check, and `repair` copied it under flags that
  said it was not encrypted; an entry encrypted or compressed some other way anywhere in the
  package is refused
  (`tests/test_what_a_command_takes.py::test_an_entry_encrypted_anywhere_in_the_package_is_refused`).
- An unused link definition after the first in a paragraph was said to be on the first one's line
  (`tests/test_what_a_command_takes.py::test_an_unused_definition_is_named_at_its_own_line`).
- A picture at a drive path such as `C:\…` was refused as a remote image; it is read as a path
  (`tests/test_what_a_command_takes.py::test_a_drive_path_is_a_path_not_a_remote_image`).
- `--force-cs-whole-doc` on a document of Thai only, and `--thai-language` on one with no Thai,
  changed nothing and said nothing; the build says so
  (`tests/test_what_a_command_takes.py::test_a_flag_that_reaches_nothing_says_so`).
- A caption's hanging indent past the text, or a caption as narrow as a small picture under
  `--caption-matches-object`, was written as a line of no width or less. The first is refused as
  `--indent` is; the second takes the text width, with a warning
  (`tests/test_what_a_command_takes.py::test_a_caption_is_never_given_less_than_an_inch`).
- A footnote's label matched only in the case it was written; it matches as a link's does
  (`tests/test_what_a_command_takes.py::test_a_footnote_label_matches_in_any_case`).
- Bare addresses are found as GitHub finds them: a Thai domain is a link, `mailto:` is part of
  its link, and punctuation or an entity at a URL's end is left out of it; `ftp://` and `xmpp:`
  stay text (`tests/test_what_a_command_takes.py::test_an_extended_autolink_is_found_as_cmark_gfm_finds_it`).
- The release could replace a published release's assets on a second run (`--clobber`), and
  packed every file under the skill's folder, tracked or not; it keeps what a release has, and
  packs what git tracks
  (`tests/test_release_is_bound_to_its_tag.py::test_a_release_never_replaces_an_asset_it_already_has`,
  `tests/test_package_skill.py::test_only_what_git_tracks_is_packed`).
- Every CI checkout left the job's token in `.git/config` for the steps after it
  (`tests/test_release_is_bound_to_its_tag.py::test_no_checkout_leaves_its_token_behind`).
- Pages said less, or other, than the code does: ADR 0039 that `--force-cs-whole-doc` marks
  `docDefaults` too, `check.md` "complex script" where the checker reads Thai (U+0E00 to U+0E7F),
  the assurance case's allowlists without the link schemes, and the limits without NFC among what
  the Unicode version decides
  (`tests/test_build.py::test_force_cs_marks_every_run_and_leaves_the_defaults_unmarked`,
  `tests/test_rules.py::test_what_the_review_found_the_pages_left_out_they_now_say`).
- `repair` said it wrote a complex-script font whenever it marked a run or wrote a twin, where it
  wrote none; it says so only where it did
  (`tests/test_what_a_command_takes.py::test_repair_says_it_wrote_a_font_only_where_it_did`).
- A picture refused for its bytes or its size was not named; the error names it
  (`tests/test_what_a_command_takes.py::test_a_picture_refused_is_named`).

## [0.2.1] - 2026-09-26

Every fix below was found in the readings of 0.2.0 on the day it was released
([record](docs/evidence/2026-09-24-three-readings-of-0.2.0.md)). **No document changes**: 0.2.1
writes byte for byte what 0.2.0 wrote, so what was read in the five applications on 0.2.0's files
holds for it. Each `Fixed` line names the test that fails without the fix (ADR 0041).

### Added

- **A finding is closed by the control that holds it** (ADR 0041). `tests/regressions.yaml` lists
  every finding closed since 0.2.0 with its class and its test, and `tests/test_regressions.py`
  holds each row, and each `Fixed` line from this release on, to naming a test there is.
- **The limits, restated** (ADR 0040, superseding 0030): what every command reads, writes and
  accepts, including what the review added — the ceilings, links, text, escaping, names.
- `profile save` and `import` say `"shadows"`, with a warning, when the name written hides a
  profile of the same name further down the search — the skill ships one named `thesis`.
- CI runs the suite on the newest runtimes the skill promises (Python 3.13, Node.js 24) beside the
  oldest.

### Changed

- **`repair` on a file with nothing to repair** answers `"ok": true` with a `clean` warning and
  writes nothing (exit 0), where it answered an error pointing at findings it did not have.
- **The build refuses** a link to anything but `http`, `https` or `mailto` (a link with no scheme
  is written as before); any format character or noncharacter, named; a caption label holding
  `"` or `\`, or a table or figure label holding a space under `--auto-numbering`; a picture
  wider or taller than 20,000 pixels; `--allow-dir` of the filesystem's root or of nothing. A
  picture is fitted to the page's height as well as its width. A link's target is written
  percent-encoded.
- `grill` asks in the language most of the message's words are in, and warns when a `from` or
  `save to` later in the message was not read.
- The release workflow builds the tag as `refs/tags/<tag>`, proves the commit, runs the lints and
  the coverage floor, and verifies the attestation against the workflow and the tag; every
  documented verify command names both.

### Fixed

- `build` and `repair` could write over their own input — by path, symbolic link or hard link
  (`tests/test_what_a_command_takes.py::test_the_input_is_never_the_output`).
- A FIFO given as Markdown, picture, profile or package hung the command; the Markdown, and
  JavaScript `repair`'s input, were read whole with no ceiling
  (`tests/test_what_a_command_takes.py::test_a_file_that_is_not_a_regular_file_is_refused_before_it_is_opened`,
  `tests/test_what_a_command_takes.py::test_a_markdown_file_past_its_ceiling_is_refused_not_read_whole`,
  `tests/test_build.py::test_one_picture_past_its_cap_is_refused_before_it_is_read_whole`).
- An argument in another encoding, or a lone surrogate in a profile, stopped Python with a trace
  and was written as U+FFFD by JavaScript
  (`tests/test_what_a_command_takes.py::test_an_argument_in_another_encoding_is_refused_the_same_way`).
- A number too long for a float stopped Python with a trace
  (`tests/test_what_a_command_takes.py::test_a_number_too_long_for_a_float_is_refused_not_a_traceback`).
- `repair --font` was written into the XML unread and unescaped
  (`tests/test_what_a_command_takes.py::test_the_font_given_to_repair_is_read_like_the_builds_and_escaped`).
- A profile name could hold what a shell reads, and `grill` handed it back in a command;
  `profile save --help` saved a profile named `--help`
  (`tests/test_what_a_command_takes.py::test_a_profile_name_is_letters_digits_dash_and_underscore`,
  `tests/test_what_a_command_takes.py::test_grill_never_hands_back_a_word_a_shell_would_read`).
- A profile with a value of the wrong type, nested past the parser, keyed `__proto__`, saying
  `"schema": true`, or not UTF-8, stopped one implementation or split them
  (`tests/test_what_a_command_takes.py::test_a_profile_that_is_not_a_profile_is_named_not_obeyed`); a failed import emptied the
  profile it replaced (`tests/test_what_a_command_takes.py::test_a_profile_is_replaced_whole_or_not_at_all`).
- `--help` after `build` or `check`, a pipe that is not UTF-8, a working directory removed, and
  any other fault left a trace where one JSON line belongs
  (`tests/test_what_a_command_takes.py::test_help_is_the_usage_line`, `tests/test_what_a_command_takes.py::test_a_pipe_that_is_not_utf8_still_gets_the_json_line`,
  `tests/test_what_a_command_takes.py::test_a_working_directory_that_is_gone_is_said_not_a_traceback`,
  `tests/test_what_a_command_takes.py::test_the_entry_answers_before_any_command_runs`).
- `repair` cut a run without `xml:space`, so the space between Thai and English stopped being
  text (`tests/test_repair_reads_xml_as_xml.py::test_a_cut_run_keeps_the_space_at_the_cut`); cut through a tab's markup and refused
  the file (`tests/test_repair_reads_xml_as_xml.py::test_a_run_with_a_tab_is_marked_whole_not_cut_through_its_markup`); cut a Thai word
  at an invisible character (`tests/test_repair_reads_xml_as_xml.py::test_an_invisible_character_inside_a_thai_word_is_not_a_place_to_cut`).
- `repair` read a `>` inside an attribute, or `<w:r />`, as the end of a tag, and gave a size in
  single quotes a twin with no value
  (`tests/test_repair_reads_xml_as_xml.py::test_a_greater_than_inside_an_attribute_is_not_the_end_of_the_tag`,
  `tests/test_repair_reads_xml_as_xml.py::test_an_empty_run_is_passed_over`, `tests/test_repair_reads_xml_as_xml.py::test_a_single_quoted_size_gets_its_twin_with_the_same_value`).
- `repair` half repaired a part under another prefix, edited around comments and CDATA, and could
  touch a picture whose bytes spelled a tag, or stop on it in JavaScript
  (`tests/test_repair_reads_xml_as_xml.py::test_a_part_under_another_prefix_is_refused_not_half_repaired`,
  `tests/test_repair_reads_xml_as_xml.py::test_a_part_holding_a_comment_or_cdata_is_left_as_it_came`,
  `tests/test_repair_reads_xml_as_xml.py::test_a_picture_is_left_byte_for_byte_whatever_its_bytes_spell`).
- `repair` compared only the body's text, and wrote a file its own checker faulted
  (`tests/test_repair_reads_xml_as_xml.py::test_the_text_of_a_header_is_compared_too`,
  `tests/test_repair_reads_xml_as_xml.py::test_a_repair_that_breaks_the_package_writes_nothing_and_is_this_versions_fault`); its
  text guard is now shown to bite (`tests/test_repair_reads_xml_as_xml.py::test_a_repair_that_changes_a_character_writes_nothing`);
  putting properties in order took seconds on a small part
  (`tests/test_repair_reads_xml_as_xml.py::test_putting_properties_in_order_takes_time_in_proportion_to_the_part`).
- A part in UTF-16 with no byte-order mark got past the DOCTYPE refusal in Python and had its
  entities expanded (`tests/test_check_holds_its_limits.py::test_a_utf16_part_is_refused_not_parsed`); a run's properties nested 500
  deep stopped `check` (`tests/test_check_holds_its_limits.py::test_a_run_nested_past_any_stack_is_read_not_a_trace`).
- A chain of 41 symbolic links embedded a picture from outside the Markdown's directory
  (`tests/test_check_holds_its_limits.py::test_forty_links_are_followed_and_the_forty_first_is_not`); the size caps were held by no
  test at their values (`tests/test_check_holds_its_limits.py::test_the_size_caps_hold_at_their_values`,
  `tests/test_check_holds_its_limits.py::test_each_limit_is_the_value_both_implementations_state`).
- A caption label holding `&` or `<` broke its field
  (`tests/test_build_writes_what_it_was_given.py::test_a_label_is_escaped_in_its_field_and_one_a_field_would_misread_is_refused`); a list
  numbered from 0 was renumbered from 1 (`tests/test_build_writes_what_it_was_given.py::test_a_list_numbered_from_zero_starts_at_zero`);
  eight thousand unclosed links took most of a minute
  (`tests/test_build_writes_what_it_was_given.py::test_two_thousand_open_links_are_read_in_a_moment`).
- The two implementations disagreed on `<ſ>`, on a small float in the JSON line, and on where
  grill splits words (`tests/test_build_writes_what_it_was_given.py::test_a_tag_name_is_ascii_in_both`,
  `tests/test_build_writes_what_it_was_given.py::test_a_small_float_is_reported_as_python_writes_it`, `tests/test_build_writes_what_it_was_given.py::test_grill_reads_the_same_words_in_both`).
- A picture declaring a vast size got an extent past the format, or one of nothing
  (`tests/test_build_writes_what_it_was_given.py::test_a_picture_is_fitted_to_the_page_and_never_to_nothing`); the math warning named
  version 0.1 (`tests/test_build_writes_what_it_was_given.py::test_math_is_said_to_be_kept_as_it_was_written_without_a_version`).
- `tools/oracle_set.py --help` made a directory named `--help`
  (`tests/test_oracle_set.py::test_a_question_is_answered_with_the_usage_and_nothing_is_made`);
  `CITATION.cff` was checked by nothing
  (`tests/test_package_skill.py::test_the_citation_names_the_release_the_changelog_names`);
  `tools/preflight.py` could not import YAML (`tests/test_release_is_bound_to_its_tag.py::test_what_the_tools_import_the_requirements_pin`).
- SKILL.md's sentences that sent an agent the wrong way — the last build's flags dropped on a
  change, exit 1 read as a defect, a user's file edited, the grill argument cut
  (`tests/test_the_docs_say_what_the_skill_does.py::test_a_change_keeps_the_flags_of_the_last_build`,
  `tests/test_the_docs_say_what_the_skill_does.py::test_exit_1_is_read_as_the_command_that_gave_it`,
  `tests/test_the_docs_say_what_the_skill_does.py::test_a_file_the_user_gave_is_changed_only_as_they_say`, `tests/test_the_docs_say_what_the_skill_does.py::test_the_grill_argument_is_passed_whole`).
- Records: a measurement with no record, a release record with no hash of its bytes, sentences of
  accepted records no longer true, two pictures of unknown origin
  (`tests/test_rules.py::test_a_dated_measurement_in_the_references_has_a_record_of_that_day`,
  `tests/test_rules.py::test_the_newest_release_record_names_the_bytes_it_read`,
  `tests/test_rules.py::test_the_records_found_stale_in_0_2_0_say_what_holds_now`,
  `tests/test_rules.py::test_every_picture_the_fixtures_carry_says_where_it_came_from`).

## [0.2.0] - 2026-09-24

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
  renumber what follows; the reference application must pass it, and on 2026-09-23 it did. Under
  this flag the list of tables and the list of figures collect **the caption's counter**
  (`TOC \c "ตาราง"`), not its style, so a caption the reader adds in Word joins the list whichever
  way it was added — References → Insert Caption gives Word's own `Caption` style, and a pasted
  caption may keep neither. `references/numbering.md` says what to update after inserting a
  chapter (every field, **Update entire table**), and how to add a caption in a ready-to-use
  document, where the numbers are text: copy a whole caption paragraph and type the number.
- WPS Writer re-checked (11.1.0.11723): both fixes of 0.1.0 hold there, the three lists fill on
  open, and what WPS draws its own way is recorded — SARA AM's placement, which ADR 0038 later traced to
  `w:bidi="th-TH"` (below). A chapter label drawn as
  Latin letters and the numbering value 1 drawn as ๕ under `--thai-digits`, read the same morning,
  did not reproduce on 2026-09-23, on the same bytes; what changed is not established. The check also
  found that the task-list boxes `☐` and `☑` were written in Segoe UI Symbol, which no Linux machine
  has, so they drew as nothing outside Windows (fixed below, ADR 0033).
- The two installers are held by tests, not only by a promise. The archive and the subtree
  `skills/thai-docx/` that `gh skill install` and `npx skills add` copy must be the same files
  **and the same bytes**; and the front matter must survive being written again the way
  `gh skill install` writes it — keys sorted, `metadata` flattened, quotes dropped — so nothing
  depends on their order, `version` keeps its two dots, and no key inside `metadata` shares a name
  with a top-level one. Both guides now say which installer gives the release and which gives
  `main`, with `--pin` and `gh skill preview`.
- `thai_docx repair IN.docx OUT.docx` — the repairs of v0.2 (ADR 0037, which restates 0032). It
  clears findings `1` (compatibility mode 15), `2` (a run marked complex script where its text is,
  and the mark taken off where it is not — off the document defaults and the styles too, without
  which a run that leaves it off only inherits it again; a run that holds both scripts is cut where
  the script changes, since attributes alone would reach about a third of the English — 462 Latin
  letters of the thesis fixture sit in Latin-only runs against 924 inside runs that hold Thai as
  well; a run carrying a field, a picture, a tab, a break or a numeric character reference is never
  cut; `--force-cs-whole-doc` marks every run instead, as the build does with it), `3`
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
  implementations, and that file now comes back as 39,415. It reaches 4.1% on the styles part that
  caused the growth, against zlib's 3.5%.
- A package can be written back as it came. `package.repack` (and `repackZip` in JavaScript) writes
  the entries in the order they had, copying the compressed bytes of every entry it was not asked to
  replace — method, checksum, sizes, date, "version made by" and attributes kept — and storing only
  the parts given anew. Every package in this repository, written back with nothing replaced, is
  byte for byte the file that went in. It is the first step of v0.2's repair (ADR 0037, which restates 0032): the
  builder's packer stores every entry, which would hand a user's own document back about twenty-two
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

- **What this release was read in, and what it was not**
  ([record](docs/evidence/2026-09-24-what-v0.2.0-was-read-in.md)). Word 365 for Windows passes
  every item on these bytes, WPS Writer and Google Docs pass where read. **Word for macOS was not
  read on them, and LibreOffice Writer only in `sample-auto`**: the maintainer released first and
  owes both. In that one document LibreOffice underlined every Thai word, because it takes the
  complex-script language from its own setting — Hindi on an English installation — not from the
  machine; `limits.md` §3 now says so and how to set it.
- **The Thai language is written only when `--thai-language` asks** (ADR 0038). Every run used to
  name `w:bidi="th-TH"`, and that one attribute is what makes WPS Writer place SARA AM (ำ) over the
  wrong letter. The default now leaves the complex-script language to the reader's machine;
  `--thai-language` names Thai for a machine with no Thai among its languages, and WPS then
  misplaces ำ again (`limits.md` §3, §7). **Every document's bytes change.**
- `SKILL.md` names `--heading-numbers` for numbers on headings, and `--auto-numbering` as added to
  it. Naming only the second, Haiku 4.5 used it in place of the first in two runs of three.

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
  `Figure Caption`, and the list collects that style with `\t` — or, under `--auto-numbering`,
  the caption's own counter with `\c`. **The bytes of every document change**; the goldens were
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
