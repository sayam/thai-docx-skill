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
(cd tests/js && npm ci --ignore-scripts)                        # the CommonMark reference and ESLint
python3 -m pytest -q tests                                      # the suite
python3 -m ruff check skills/thai-docx/scripts tools tests      # the Python lint
tests/js/node_modules/.bin/eslint --config tests/js/eslint.config.cjs js   # the JavaScript lint
python3 -m coverage run -m pytest -q tests && python3 -m coverage combine -q && python3 -m coverage report
```

The gates come from [verifiable-gates](https://github.com/sayam/verifiable-gates). The doctor
also refuses a `tools/` file that differs from what was installed (`tools/installed.json`).

CI runs `scans`, `commits`, `tests` (at least 97% coverage, branches included), `lint` (the
coding standards below) and `deps` (the dependencies below) on every pull request; `main` takes a
change only when all five pass, and a contributor's pull request also needs a code owner's approval (`.github/CODEOWNERS`,
`docs/adr/0018`).

## Coding standards

- **Python** follows [PEP 8](https://peps.python.org/pep-0008/) as ruff checks it: pycodestyle's
  errors and warnings (`E`, `W`) with lines of at most 150 characters — where the code already
  stood — plus pyflakes (`F`) and bugbear (`B`). `ruff.toml` holds the settings.
- **JavaScript** in `js/` follows ESLint's recommended rules (`@eslint/js`). Each part is linted
  with the names the other parts give it in the bundle (`tests/js/eslint.config.cjs`). An exception
  is an `eslint-disable-next-line` comment on that line, with its reason. The generated
  `scripts/thai_docx.js` is not linted.
- The `lint` job runs both on every pull request, and fails on any finding.

## Dependencies

- **At run time: none.** The skill uses the Python standard library, or one JavaScript file that
  needs only `TextEncoder` and `TextDecoder` (`docs/adr/0008`). A change that adds a run-time
  dependency is a change of design and needs a decision record first.
- **For development** (tests, lint, coverage, the CommonMark reference): a tool is taken only if it
  has an OSI-approved licence compatible with MIT and is actively maintained.
- **How they are obtained:** Python tools only through `requirements/dev.txt` with
  `--require-hashes` (its header says how to refresh a hash); npm packages only through
  `tests/js/package-lock.json` with `npm ci --ignore-scripts`; GitHub Actions only pinned by commit
  SHA, and container images only by digest, with the version in a comment. The gates
  `ci-tools-hash-pinned` and `actions-sha-pinned` refuse anything else.
- **How they are updated:** by hand, in a pull request of its own that names the new version and
  its hash. No bot opens update pull requests; Dependabot alerts are on and are read.
- **How they are checked:** the `deps` job checks every push and pull request against the OSV
  database for known vulnerabilities and malicious packages, and a finding fails it. `deps` is
  required before merge.
- **Thresholds:** a known vulnerability of high or critical severity in a dependency is fixed
  within 7 days, medium within 30 days, low at the next update. A licence finding is fixed by
  removing the dependency.
- **No release** is made while a finding is open: the release workflow runs the same check on
  the tag.

## Static analysis

CodeQL's security-extended queries run on every pull request and push to `main` and weekly
(`.github/workflows/codeql.yml`). A pull request with an open alert of **medium security severity
or higher** cannot merge. Lower alerts are triaged within 30 days. An alert is dismissed only with
a written reason why it is not exploitable here; the reason stays on the alert.

## Where things are

- `skills/thai-docx/` — the skill itself; the only part that ships
- `js/` — the sources of `scripts/thai_docx.js`; `python3 tools/bundle_js.py` builds it
- `tests/` — the suite; `gates.yaml` names the gate each test file holds
- `docs/guide/` — the user guides, in Thai and English
- `docs/adr/` — the decision records; `docs/adr/README.md` is their index
- `docs/evidence/` — what each gate was seen to catch
- `docs/handoff/` — the diagnosis this skill started from, kept verbatim
- `docs/templates/decision.md` — the shape of a new record
- `SOURCES.md` — the sources the records cite, by id
- `tools/` — verifiable-gates 0.10.0 (Apache-2.0), plus this project's
  `bundle_js.py`, `gen_settings_docs.py`, `measure_xml_names.py`, `oracle_set.py` and `package_skill.py`

Only `skills/thai-docx/`, the README, the licence, the changelog, `PROMPT.md` and `PROMPT.th.md` reach a user;
the rest is marked `export-ignore` (`docs/adr/0018`).

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
  without gaps (below, "Add a decision"); a record is restated by a new one, never
  edited into something else.
- **Evidence for a new gate.** A gate in `gates.yaml` names the file in `docs/evidence/` that
  shows its planted defects red.
- **Synthetic content only** in fixtures, evidence and examples — no real people, documents or
  institutions.

## Add a decision

1. Copy `docs/templates/decision.md` to `docs/adr/NNNN-short-slug.md`, taking the next number —
   no gaps, no repeats.
2. Add its row to `docs/adr/README.md`. The doctor is red until you do.
3. Give every outside source it leans on a row in `SOURCES.md` and cite it by id, as `[S1]`.
4. A record that replaces an older one says `Supersedes: NNNN`, and the older one gets
   `Superseded by: NNNN` — the doctor reads both sides.

## Before a release

`python3 tools/oracle_set.py OUT_DIR` writes the documents to open in the five office
applications — each variant once per application, named `<variant>-<application>.docx`, byte for
byte the goldens — and `CHECKLIST.md` to tick (`docs/adr/0012`). Word 365 for Windows is the
reference. `python3 tools/package_skill.py --tag vX.Y.Z` must pass, and the suite fails until the
archive name in the README and the guides (`thai-docx-X.Y.Z.zip`) carries the new version.

## Commits

Conventional Commits, a subject of at most 72 characters, signed off with `git commit -s`
(DCO 1.1), and no assistant trailers such as `Co-Authored-By` (`docs/adr/0013`). Check a
branch with `python3 tools/lint_commits.py --range main..HEAD`. Pull requests are merged by
rebase, so each commit should stand on its own.

## License

By contributing you agree that your contribution is licensed under the MIT License of this
repository (`LICENSE`); files under `tools/` keep the licenses `tools/LICENSE` names.
