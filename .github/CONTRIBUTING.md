# Contributing to thai-docx-skill

Thank you for helping. This page is for changing the skill; to use it, read the
[user guide](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en.md)
([ภาษาไทย](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/th.md)). Everyone who
takes part follows the [code of conduct](https://github.com/sayam/thai-docx-skill/blob/main/CODE_OF_CONDUCT.md); how decisions are made is in
[GOVERNANCE.md](https://github.com/sayam/thai-docx-skill/blob/main/GOVERNANCE.md).

**Read [`docs/rules.md`](https://github.com/sayam/thai-docx-skill/blob/main/docs/rules.md) first.**
It holds the rules a change is decided by — what this skill answers for, what leaves it, what it
must never introduce, and the compatibility contract the five office applications are held to.
Against a rule means the change is not made, and the reason is written down. The Thai in that file
is the rule; the English below it is a translation for reference. A decision record says how a rule
was applied; it does not overrule one.

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
coding standards below), `deps` (the dependencies below), `pr-description` (a description
credits nobody who did not sign) and `tests-newest` (the suite on the newest Python and Node the
skill promises) on every pull request; `main` takes a change only when all seven pass and CodeQL raises no alert of medium severity or higher
(below, "Static analysis"), and a contributor's pull request also needs a code owner's approval (`.github/CODEOWNERS`,
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
- `docs/rules.md` — the rules a change is decided by, in Thai, with an English translation
- `docs/guide/` — the user guides, in Thai and English
- `docs/adr/` — the decision records; `docs/adr/README.md` is their index
- `docs/evidence/` — what each gate was seen to catch
- `docs/handoff/` — the diagnosis this skill started from, kept verbatim
- `docs/templates/decision.md` — the shape of a new record
- `SOURCES.md` — the sources the records cite, by id
- `tools/` — verifiable-gates 0.10.0 (Apache-2.0), plus this project's
  `bundle_js.py`, `gen_settings_docs.py`, `lint_pr_body.py`, `measure_xml_names.py`, `oracle_set.py` and `package_skill.py`

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
- **A fixed finding is a row, and a `Fixed` line names its test.** Add the finding to
  `tests/regressions.yaml` with its class and its test, and name the test in the changelog's
  `### Fixed` line as `tests/<file>.py::<test>` — a fault is closed by what holds it closed, not
  by the change (ADR 0041).
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
- **SPDX lines on a new source file.** A new file in `js/`, the Python package, `tests/` or this
  project's tools starts with SPDX comment lines: `SPDX-FileCopyrightText: <year> <your name>`
  — you keep the copyright of what you write; add your own line to a file you change substantially —
  then `SPDX-License-Identifier: MIT` (`tests/test_licensing.py`).
- **Synthetic content only** in fixtures, evidence and examples — no real people, documents or
  institutions.

## How a pull request is reviewed

Every pull request is reviewed by a code owner before it merges; the maintainer's own pull
requests are reviewed against the same list by the maintainer and by the required checks
(`scans`, `commits`, `tests`, `lint`, `deps`, `pr-description`, `tests-newest`) and CodeQL's alerts ("Static analysis" above). A
review looks at:

1. **The claim.** The description says what changes for a user and why; a design change links
   its ADR.
2. **The test that went red.** A new or changed test fails without the change — the pull request
   says how that was seen — and passes with it.
3. **Both implementations.** Python and `js/` change together; the bundle is regenerated; parity
   holds.
4. **The goldens.** Unchanged, or changed on purpose with the parts named and a request to open the
   files in Word 365 for Windows.
5. **The limits of ADR 0040.** No network, subprocess, `eval`, environment read or new write path;
   input from a user, an agent or a file is checked against an allowlist before use. A change that
   moves a boundary updates `docs/assurance-case.md`.
6. **What the agent reads.** SKILL.md and `references/` stay true (the tests say so) and SKILL.md
   stays under 12,000 bytes; wording an agent follows is changed only with a note of how it was
   tried on an agent.
7. **Documentation.** The user guides, the settings reference and the CHANGELOG say what changed.
8. **Dependencies and workflows.** New CI tools are pinned by hash and actions by commit SHA;
   workflow permissions stay least-privilege.

A reviewer approves, asks for changes with the item number, or explains why the change is declined.
Nothing merges with a failing required check.

## Add a decision

1. Copy `docs/templates/decision.md` to `docs/adr/NNNN-short-slug.md`, taking the next number —
   no gaps, no repeats.
2. Add its row to `docs/adr/README.md`. The doctor is red until you do.
3. Give every outside source it leans on a row in `SOURCES.md` and cite it by id, as `[S1]`.
4. A record that replaces an older one says `Supersedes: NNNN`, and the older one gets
   `Superseded by: NNNN` — the doctor reads both sides. A record that changes part of an older one
   says `Amends: NNNN (what)`, and the older one gets `Amended by: NNNN (what)` — the tests read
   both sides (`tests/test_adr_amendments.py`).
5. An accepted record is never rewritten. When a sentence of it stops being true of the code, it
   keeps its words and gains a dated line beneath them, `> **Later (YYYY-MM-DD):** what holds now`.

## Before a release

`python3 tools/oracle_set.py OUT_DIR` writes the documents to open in the five office
applications — each variant once for every application it is opened in (`sample-auto` in Word 365
for Windows only, ADR 0036), named `<variant>-<application>.docx`, byte for
byte the goldens — and `CHECKLIST.md` to tick (`docs/adr/0012`). Word 365 for Windows is the
reference. `python3 tools/package_skill.py --tag vX.Y.Z` must pass, and the suite fails until the
archive name in the README and the guides (`thai-docx-X.Y.Z.zip`) carries the new version.

## Commits

Conventional Commits, a subject of at most 72 characters, signed off with `git commit -s`
(DCO 1.1), and no assistant trailers such as `Co-Authored-By` (`docs/adr/0013`). Check a
branch with `python3 tools/lint_commits.py --range main..HEAD`. Pull requests are merged by
rebase, so each commit should stand on its own.

**A pull request's description is held to the same rule.** It credits nobody who did not sign: no
line opens with `Co-authored-by:` or `Claude-Session:`, with an assistant's "Generated with …"
footer, or with a link to its session. Turn the footer off in the tool that writes it, or delete
it before you open the pull request. Saying what the rule refuses is fine — a mention inside a
sentence, or quoted in backticks, opens no line. The `pr-description` check runs when a pull
request is opened or pushed to, and again each time its description is edited, which is how a
refused one is fixed. Check yours with `python3 tools/lint_pr_body.py --file description.md`.

## License

By contributing you agree that your contribution is licensed under the MIT License of this
repository (`LICENSE`); files under `tools/` keep the licenses `tools/LICENSE` names.
