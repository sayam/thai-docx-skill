# Contributing to thai-docx-skill

Thank you for helping. This page is for changing the skill; to use it, read the
[user guide](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en.md)
([ภาษาไทย](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/th.md)).

## Ask first, in an issue

Open an [issue](https://github.com/sayam/thai-docx-skill/issues) before a large change, and
always for a Word file that renders wrong: attach a synthetic Markdown file that shows it,
the flags, the application and its version. Never attach a real person's document. A
security problem goes to private reporting instead (`.github/SECURITY.md`).

## Set up

```sh
python3 tools/gates_doctor.py                                   # the gates
python3 -m pip install --require-hashes -r requirements/dev.txt
(cd tests/js && npm ci --ignore-scripts)                        # the CommonMark reference
python3 -m pytest -q tests                                      # the suite
python3 -m ruff check skills/thai-docx/scripts tools tests      # the lint
```

CI runs `scans`, `commits`, `tests` (under coverage, at least 97% of branches) and `lint`
on every pull request; `main` takes a change only when all four pass, and a contributor's
pull request also needs a code owner's approval (`.github/CODEOWNERS`, `docs/adr/0018`).

## What a pull request carries

- **Both implementations.** Every behaviour exists in Python (`skills/thai-docx/scripts/thai_docx/`)
  and JavaScript (`js/`, bundled by `python3 tools/bundle_js.py`) with the same bytes out
  (`docs/adr/0008`). The parity tests in `tests/test_js_parity.py` hold them together; add a
  case for what you change, with the value where the two runtimes' types differ (a whole
  float, a path not in normal form).
- **A test that fails without the change.** Plant the defect your change prevents and watch
  the test go red before you call it held.
- **Goldens change only on purpose.** `tests/golden/` is byte for byte what the build gives.
  A refactor leaves them alone; a change that alters them rebuilds them, says which parts
  changed and why, and asks for the files to be opened in Word 365 for Windows, the reference
  application.
- **Settings through the registry.** A new setting is one entry in `settings.py` and
  `js/45-settings.js` (`docs/adr/0028`); run `python3 tools/gen_settings_docs.py` to
  regenerate `references/settings.md`.
- **SKILL.md stays small.** It must stay under 12,000 bytes; move tables into
  `skills/thai-docx/references/` rather than raise the ceiling, and link every reference.
- **A record for a decision.** A change of design is an ADR in `docs/adr/`, numbered next
  without gaps (see the README, "Adding a decision"); a record is restated by a new one, never
  edited into something else.
- **Evidence for a new gate.** A gate in `gates.yaml` names the file in `docs/evidence/` that
  shows its planted defects red.
- **Synthetic content only** in fixtures, evidence and examples — no real people, documents or
  institutions.

## Commits

Conventional Commits, a subject of at most 72 characters, signed off with `git commit -s`
(DCO 1.1), and no assistant trailers such as `Co-Authored-By` (`docs/adr/0013`). Check a
branch with `python3 tools/lint_commits.py --range main..HEAD`. Pull requests are merged by
rebase, so each commit should stand on its own.

## License

By contributing you agree that your contribution is licensed under the MIT License of this
repository (`LICENSE`); files under `tools/` keep the licenses `tools/LICENSE` names.
