# 2026-09-16 — the settings registry: the same behaviour on 60,000 command lines, and 9 planted defects

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

## Not proved here

- That an agent reads `references/settings.md` as it read the table in SKILL.md: SKILL.md
  still carries its own table until the SKILL.md phase of the redesign, which reruns the agent
  cases (L-0007).
- The reference's wording is Python-only (`doc` in each entry): the JavaScript never prints it.

Harness, planted texts, logs and the comparison (`diff_parse.py OLD_PACKAGE_DIR NEW_PACKAGE_DIR`):
`.local/work/2026-09-16-redesign/mutations-registry/`.
