# thai-docx-skill

[![CI](https://img.shields.io/github/actions/workflow/status/sayam/thai-docx-skill/gates.yml?branch=main&label=CI)](https://github.com/sayam/thai-docx-skill/actions/workflows/gates.yml)
[![Skill: MIT](https://img.shields.io/badge/skill-MIT-blue)](https://github.com/sayam/thai-docx-skill/blob/main/LICENSE)
[![Runs on Python 3.11+ · Node.js 22](https://img.shields.io/badge/runs_on-Python_3.11%2B_%C2%B7_Node.js_22-blue)](https://github.com/sayam/thai-docx-skill/blob/main/.github/workflows/gates.yml)

An [Agent Skill](https://agentskills.io/specification) that makes Word (.docx)
documents with Thai or mixed Thai–English text render correctly: no spelling
squiggles under every Thai word, Thai lines that wrap inside words, bullets and
bold that work. The agent writes Markdown; one bundled command builds the
document and checks it without changing a character of the content.

**Status: v0.1.0.** Checked in the office applications of `docs/adr/0012`, with Word 365
for Windows as the reference; `CHANGELOG.md` lists what it does.

## Use the skill

**Step-by-step guides, every scenario from a plain request to editing a saved profile:**
[ภาษาไทย](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/th.md) ·
[English](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en.md)

You need only `skills/thai-docx/`. Nothing else in this repository is loaded by an
agent, and none of it is needed to run the skill.

- **A release archive.** Each release carries `thai-docx-<version>.zip`, holding the
  `thai-docx/` folder and nothing else. Upload it where your client takes skills, or
  unpack it into your agent's skills directory — for Claude Code, `~/.claude/skills/`
  or a project's `.claude/skills/`.
- **With git, the skill alone:**

  ```sh
  git clone --depth 1 --filter=blob:none --sparse https://github.com/sayam/thai-docx-skill.git
  cd thai-docx-skill
  git sparse-checkout set --no-cone /skills/thai-docx/
  ```

"Download ZIP" and a release's source archives also leave the development files out
(`.gitattributes`).

Then ask for a Word document with Thai in it. The skill builds at once with announced
defaults; say `thai-docx grill` to be asked about font, page and layout first.
Settings that suit your work can be kept as a profile and used again with
`--profile NAME`; `profile export` writes the file to hand to someone else, who takes it
with `profile import` (`docs/adr/0024`). `thai-docx grill from thesis save to thesis-v1`
asks the questions again starting from a profile and keeps the answers under a new name
(`docs/adr/0029`).
Python 3.11+ or Node.js is enough; nothing is installed and nothing reaches the network.

## Develop the skill

A clone or a fork carries everything: the tests, the decision records and the gates
from [verifiable-gates](https://github.com/sayam/verifiable-gates). They travel with
anyone who works on the skill because a pull request is held to them:

```sh
python3 tools/gates_doctor.py                                   # the gates
python3 -m pip install --require-hashes -r requirements/dev.txt
(cd tests/js && npm ci --ignore-scripts)                        # the CommonMark reference
python3 -m pytest -q tests                                      # the suite
```

CI runs both on every push and pull request, and lints every commit they add.
`main` accepts changes only through a pull request that passes `scans`, `commits` and
`tests`; a contributor's pull request also needs a code owner's approval
(`.github/CODEOWNERS`) — including any change to the workflow, the gate registry or the
tools that decide them (`docs/adr/0018`).
The doctor also refuses a `tools/` file that differs from what was installed
(`tools/installed.json`).

Before a release, `python3 tools/oracle_set.py OUT_DIR` writes the documents to open in
the five office applications — each variant once per application, named
`<variant>-<application>.docx`, byte for byte the goldens — and `CHECKLIST.md` to tick
(`docs/adr/0012`).

## Where things are

- `skills/thai-docx/` — the skill itself; the only part that ships
- `js/` — the sources of `scripts/thai_docx.js`; `python3 tools/bundle_js.py` builds it
- `tests/` — the suite; `gates.yaml` names the gate each test file holds
- `docs/adr/` — the decision records; `docs/adr/README.md` is their index
- `docs/evidence/` — what each gate was seen to catch
- `docs/handoff/` — the diagnosis this skill started from, kept verbatim
- `docs/templates/decision.md` — the shape of a new record
- `SOURCES.md` — the sources the records cite, by id
- `tools/` — verifiable-gates 0.10.0 (Apache-2.0), plus this project's
  `bundle_js.py`, `measure_xml_names.py` and `package_skill.py`

## Adding a decision

1. Copy `docs/templates/decision.md` to `docs/adr/NNNN-short-slug.md`, taking
   the next number — no gaps, no repeats.
2. Add its row to `docs/adr/README.md`. The doctor is red until you do.
3. Give every outside source it leans on a row in `SOURCES.md` and cite it by
   id, as `[S1]`.
4. A record that replaces an older one says `Supersedes: NNNN`, and the older
   one gets `Superseded by: NNNN` — the doctor reads both sides.

## Commits

Conventional Commits, signed off with `git commit -s`, and no assistant
trailers — see `docs/adr/0013`.

## License

MIT — see `LICENSE`. The verifiable-gates files under `tools/` are Apache-2.0, and the
rule texts in `tools/overlay.json` CC BY 4.0 — see `tools/LICENSE`, which names each file.
