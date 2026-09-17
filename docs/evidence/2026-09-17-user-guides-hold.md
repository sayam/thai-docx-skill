# 2026-09-17 — the user guides hold: links, both languages, commands run, the archive's version

What this proves: the user guides, now a home page and four pages per language
(`docs/guide/{th,en}.md` and `docs/guide/{th,en}/install.md`, `scenarios.md`, `command-line.md`,
`troubleshooting.md`), and the README cannot drift from the skill without the suite going red:
a link between pages must reach a page and a heading that exist, the Thai and English pages must
keep the same sections, every command on the command-line pages and in the README must run from
the release archive and succeed, a Node.js line must give the file of the Python line before it,
the Markdown examples must build without a warning, and the archive they name must carry the version in SKILL.md.

Environment: Linux, Python 3.13 (`.venv`), Node.js 24; prepared on a copy of `main` (f31883e)
with pull requests #5, #6 and #7 applied (216 passed), then run again on `main` (c0b48e0) after
#5 to #8 were merged. Suite: 217 passed (212 before, plus five tests). `tools/gates_doctor.py` passes; `ruff check` passes.

## The tests

In `tests/test_skill_md.py`:

- `test_the_user_guides_say_what_the_skill_does` — as before (grill examples read by the script
  as the guide says, only real flags, scenarios 1–13 in both languages), now over every page.
  Lines that run another program (`npx skills`, `gh skill`, `gemini skills`, `--version`) are left
  out of the flag check.
- `test_the_user_guides_link_to_what_is_there_in_both_languages` — every relative link outside a
  code block reaches a file, every `#anchor` a heading, by the slug GitHub gives it; the two
  languages have the same `##` and `###` sections page by page. The slug function was compared
  with `github-slugger` 2 on all 96 headings of the guides: identical.
- `test_the_command_line_guide_runs_as_written_from_the_download` — the `sh` blocks of the README
  and of both command-line pages, with the report from the Thai page, run from the unpacked
  archive in a home of the test's own; each `python3` or `node` line exits 0 with `"ok": true` and
  nothing on stderr.
- `test_the_markdown_the_guides_show_builds` — the four Markdown examples of the scenarios pages
  build from the archive with no error and no warning.
- `test_the_archive_the_readme_and_guides_name_is_this_version` — every `thai-docx-X.Y.Z.zip`
  named in the README, the guides and the two prompt pages is SKILL.md's `metadata.version`.
- `test_the_prompts_for_chat_apps_give_the_same_rules` — `PROMPT.md` (below its line) and the
  copy box of `PROMPT.th.md` both name SKILL.md, the build command, python-docx and
  `thai-docx grill`, number five rules, use only real flags, and link each other.

## Planted defects

Twelve changes, each made alone, the file restored after.

| file | planted | red |
|---|---|---|
| `docs/guide/th.md` | a scenario anchor shortened | links |
| `docs/guide/en/install.md` | the language link to a page that does not exist | links |
| `docs/guide/th/install.md` | the `## Cursor` heading removed | links (anchor and section parity) |
| `docs/guide/en/command-line.md` | `--size` written `--sizes` | flags, commands |
| `docs/guide/th/command-line.md` | `profile show` of a profile that does not exist | commands |
| `README.md` | the Node.js line given `--toc` instead of the Python line's `--page-numbers` | commands (not the same file) |
| `README.md` | the archive named `thai-docx-0.1.1.zip` | version |
| `docs/guide/en/scenarios.md` | `thai-docx grill` removed from scenario 5's example | grill examples |
| `docs/guide/th/scenarios.md` | `## สถานการณ์ที่ 13` renamed | scenarios, links |
| `docs/guide/en/scenarios.md` | a `<span>` in the Markdown example | Markdown examples |
| `PROMPT.th.md` | the python-docx rule rewritten to allow any library | prompts |
| `PROMPT.th.md` | the archive named `thai-docx-0.0.9.zip` | version |

The first version of the command test keyed builds by their flags, so the README's Node.js line
with other flags passed; it now compares each Node.js build with the Python build before it.

## Not proved here

The install steps for each application follow the makers' documentation as read on 2026-09-17;
the guides say which were tried. A test cannot open those applications.
