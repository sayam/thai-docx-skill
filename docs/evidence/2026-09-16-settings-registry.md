# 2026-09-16 — the settings registry: the same behaviour on 60,000 command lines, what a setting needs, and 18 planted defects

What this proves: moving the twenty-six settings into one registry per implementation
(ADR 0028) changed no behaviour — every golden keeps its bytes, the two implementations
still agree, and the registry's parser answers exactly as the hand-written parser did — and
the gate `settings-in-one-registry` fails when the registry, its JavaScript twin or the
reference generated from it drifts.

Environment: Linux, Python 3.13.3, pytest 8.4.2, Node.js 24.15. Content synthetic.

## 1. Nothing changed

- **Goldens and parity:** the whole suite, 202 passed, with the five goldens byte for byte,
  `test_build_gives_the_same_result_and_bytes` and `test_command_line_is_the_same`
  unchanged.
- **The parser, compared.** The old `build.parse_args` and `settings_json` and the
  registry's were loaded side by side and given 60,000 seeded command lines (seed 28): every
  flag, `--flag value` and `--flag=value`, values in and out of range, empty, control
  characters, over-long text, unknown flags, zero to three positionals. The outcome of each —
  the options, the reported settings, the positionals and allowed directories, or the refusal's
  words — was compared: **60,000 the same, 0 different.** To see that the comparison could
  see a difference, `--line-spacing` was given a range of 1 to 4 in the registry: 34 command
  lines differed, the first `--line-spacing 3.5`.
- **One visible change:** the usage line lists the flags in registry order, which is the
  order of the defaults and of the reported settings. It is printed only when the command
  has the wrong number of files.

## 2. Planted defects

Harness as in `2026-09-16-adr-0027-mutations.md`: one exact text replaced, the bundle rebuilt,
the whole suite run, every red test listed, the file restored and every hash checked; a
control run at the end.

| # | planted defect | red | named by |
|---|---|---|---|
| 0 | Python: an entry carries a field the JavaScript's does not | 1 | both implementations hold the same entries |
| 1 | JS: a default differs between the implementations | 6 | same entries; parity; SKILL.md |
| 2 | JS: a refusal's words differ | 3 | same entries; parity |
| 3 | Python: the reference's wording changed without regenerating it | 1 | the reference is generated |
| 4 | Python: an example that changes another setting | 1 | every example changes its own setting |
| 5 | Python: the reference states a default the registry does not have | 2 | the reference states each default; generated |
| 6 | Python: the usage line leaves out a flag | 4 | every flag once; parity; profiles; SKILL.md |
| 7 | Python: a setting no longer says what it needs | 4 | same entries; build; parity |
| 8 | Python: the report leaves a setting out | 6 | parser, report and profile from the registry; build; parity |

All 9 red; control run green (202 passed), every hash back. Defects 0, 3, 4 and 5 are held by
the new test alone: no other test looks at the entries' shape or at the reference's words.

## 3. What a setting needs, measured

The "changed nothing" warning may only be said when it is true. Before any setting was given
a structure it needs, every setting was built on ten documents (plain; headings; a table; a
table caption; a figure caption; a list and a footnote; chapters; appendices; front pages;
a `<!-- toc -->` comment) with its example flag and without, and the two sha256 compared.
What the measurement changed against the plan:

- `--toc`, `--heading-numbers` and `--table-size` change the file on every document — a TOC
  field, heading numbering, a `TableText` style — so they need nothing.
- `--chapter-label` changes `word/numbering.xml` as soon as a `<!-- chapters -->` or
  `<!-- appendices -->` comment is there, with no heading under it; it needs the comment, not a
  numbered heading. `--chapter-title-on-new-line` needs the numbered heading.
- `--front-page-numbers` needs a `<!-- front -->` region, which a front comment with nothing
  after it does not make.

`test_a_flag_is_said_to_have_changed_nothing_exactly_when_it_changed_no_byte` repeats the
measurement on eleven documents for every setting that needs a structure, holds the warning
to it in both directions, and fails unless each setting is seen both warned about and not.

The warning found a real duplicate in a release variant: `tools/oracle_set.py`'s
`sample-layout` passes `--toc` to the thesis, which places its own `<!-- toc -->`, so the golden
`thesis-layout.docx` holds two tables of contents. Its bytes are unchanged here (a refactor
keeps goldens); the test now names the warning, and removing the flag is a golden change of
its own.

| # | planted defect | red (whole suite) | named by |
|---|---|---|---|
| 9 | Python: every document taken to have a table | 4 | changed nothing exactly when no byte changed; one warning per structure |
| 10 | Python: `--appendix-numbers` says nothing when it changed nothing | 5 | same entries; reference generated; one warning per structure |
| 11 | Python: `--chapter-label` waits for a numbered heading | 5 | changed nothing exactly …; same entries; reference; one warning … |
| 12 | Python: one warning per flag, not per structure | 3 | one warning per structure |
| 13 | Python: a second table of contents kept quiet | 3 | a duplicate is named |
| 14 | Python: a setting left at its default warned about | 17 | changed nothing exactly …; one warning … |
| 15 | Python: a front comment with nothing after it counts as a front region | 2 | changed nothing exactly … |
| 16 | JS: every document taken to have numbered headings | 1 | parity (command line) |
| 17 | JS: flags joined without "and" | 2 | parity (build, command line) |

All red; control run green (204 passed), every hash back
(`.local/work/2026-09-16-redesign/mutations-needs/`).

## Not proved here

- That an agent reads `references/settings.md` as it read the table in SKILL.md: SKILL.md
  still carries its own table until the SKILL.md phase of the redesign, which reruns the agent
  cases (L-0007).
- The reference's wording is Python-only (`doc` in each entry): the JavaScript never prints it.

Harness, planted texts, logs and the comparison (`diff_parse.py OLD_PACKAGE_DIR NEW_PACKAGE_DIR`):
`.local/work/2026-09-16-redesign/mutations-registry/`.
