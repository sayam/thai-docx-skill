# Architecture

How thai-docx is put together: the parts, what flows between them, and the properties the design
holds. The reasons are in the decision records linked from each part.

## The pieces a user receives

```
thai-docx/                     the skill folder (the release archive holds only this)
├── SKILL.md                   what the agent reads first: rules, the build, when to read more
├── references/*.md            read only when needed: settings, Markdown, chapters, profiles,
│                              heading styles, grill questions, check codes, JS sandbox
├── scripts/thai_docx/         the Python implementation (standard library only)
├── scripts/thai_docx.js       the JavaScript implementation, one generated file
├── assets/*.json              fixed XML fragments and data shared by both implementations
└── LICENSE.txt, LICENSES/
```

An agent (Claude, Codex, Copilot, …) reads SKILL.md, writes Markdown, and runs one command. Nothing
else in the repository is needed at run time ([ADR 0002](adr/0002-one-public-repository-per-skill.md),
[0018](adr/0018-users-get-the-skill-contributors-get-the-gates.md)).

## Actors and what they do

| actor | actions |
|---|---|
| user | asks for a document, answers the interview, keeps and shares profiles, opens the result |
| AI agent (model) | reads SKILL.md and references, writes the Markdown, runs the commands, reports settings and warnings |
| client app and its sandbox (Claude, Codex, Copilot, …) | loads the skill folder, runs the commands with the user's or sandbox's rights, asks for approval where it does so |
| Python or JavaScript scripts | parse, lay out, write, pack, check, compare; read the Markdown, images and profiles; write the output and profile files (limits: ADR 0025) |
| file system | the Markdown file's tree, `--allow-dir` directories, `~/.thai-docx/profiles/`, `./.thai-docx/profiles/`, the output path |
| office application (Word, LibreOffice, Google Docs, WPS) | opens the .docx; updates fields when the reader asks |
| contributor and maintainer | propose, review and merge changes through pull requests held to the gates |
| CI (`gates.yml`) | runs scans, commit lint, the suite under coverage, and lint on every push and pull request |
| release workflow (`release.yml`) | re-checks the tag, packs the skill folder, attests it with GitHub's OIDC identity (Sigstore), verifies, attaches |
| Zenodo | archives the source of each release and assigns a DOI |

The JavaScript file `scripts/thai_docx.js` is generated but committed: clients load the skill folder
as it is, with no build step, so the file must be in it. It stays readable source, and a test rebuilds
it from `js/` and fails on any byte of difference.

## The commands

| command | does | modules (Python · JavaScript) |
|---|---|---|
| `build IN.md OUT.docx [flags]` | Markdown to a .docx | `build`, `markdown`, `layout`, `writer`, `parts`, `package`, `check`, `fidelity`, `settings` · `53-build`, `40-markdown`, `48-layout`, `50-writer`, `51-parts`, `10-zip`, `30-check`, `52-fidelity`, `45-settings` |
| `check FILE.docx` | reports the causes of broken Thai in any .docx | `check`, `package`, `ooxml` · `30-check`, `10-zip`, `20-xml` |
| `profile list/show/save/export/import` | settings a user keeps and shares | `profiles`, `settings` · `55-profiles` |
| `grill --said "MESSAGE"` | decides whether to ask questions, and which | `grill`, `settings` · `56-grill` |

Each prints one JSON line and exits 0 (done) or 2 (input refused, with the reason). Exit 1
means findings, and whose depends on the command: for `build` a defect of the skill (the file it
made failed its own check, so nothing was written); for `check` a problem in the user's file.

## The build, step by step

```
Markdown ──parse──▶ blocks ──lay out──▶ sections, numbering ──write──▶ XML parts ──pack──▶ .docx bytes
                                                                                          │
                              refuse, write nothing ◀── fail ── check + fidelity ◀────────┘
                                                                  │ pass
                                                                  ▼
                                                           write OUT.docx, print JSON
```

1. **Parse** a closed Markdown dialect: CommonMark and GitHub's tables, strikethrough, autolinks,
   task lists and footnotes; anything else stops the build and names the line
   ([0022](adr/0022-markdown-accepted-restated.md)). The parser is held to commonmark.js and
   cmark-gfm ([0015](adr/0015-parser-held-to-two-reference-implementations.md)).
2. **Settings** come from one registry: defaults, then a profile, then flags
   ([0028](adr/0028-settings-in-one-registry-grouped-by-what-they-need.md),
   [0024](adr/0024-profiles-are-data-saved-and-shared.md)).
3. **Lay out** regions, sections, chapter and appendix numbering, captions and lists
   ([0021](adr/0021-regions-sections-captions-and-lists.md)).
4. **Write** WordprocessingML that marks Thai as complex script and avoids the five causes of broken
   Thai ([0004](adr/0004-thai-is-complex-script-five-causes.md)), fixing rendering with attributes,
   never by changing text ([0023](adr/0023-fidelity-transformations-restated-again.md)).
5. **Pack** a zip with stored entries and fixed metadata, so the bytes never vary
   ([0017](adr/0017-files-read-by-stated-rules.md)).
6. **Check** the package with the same checker users run, and **compare** its text with the
   Markdown character for character. Only a package that passes both is written.

## Properties the design holds

| property | how it is held |
|---|---|
| Same bytes everywhere: same input → same sha256 on every run, machine and runtime | no clock, host or user name in any part; stored zip entries; goldens in `tests/golden`; parity tests ([0008](adr/0008-two-zero-dependency-implementations-byte-identical.md)) |
| Zero run-time dependencies | Python standard library; one JS file needing only `TextEncoder`/`TextDecoder` |
| The user's text is never changed | the fidelity check on every build |
| Limited reach | no network, subprocess or eval; writes only named paths; bounded reads ([0025](adr/0025-script-limits-restated-for-profiles.md)) — see the [assurance case](assurance-case.md) |
| The script, not the agent, decides the interview | `grill --said` reads the user's words ([0029](adr/0029-grill-from-a-profile-save-as-another.md)) |
| Documentation matches the code | tests run SKILL.md's commands, the generated settings reference and the user guides |

## The repository around it

| path | role |
|---|---|
| `js/` | JavaScript sources; `tools/bundle_js.py` builds `scripts/thai_docx.js` |
| `tests/` | the suite; `tests/js` holds the CommonMark reference for the parser tests |
| `gates.yaml`, `tools/` | verifiable-gates: each gate, its test or scanner, its evidence |
| `docs/adr/`, `docs/evidence/`, `SOURCES.md` | decisions, what each gate was seen to catch, outside sources |
| `.github/workflows/` | `gates.yml` (scans, commits, tests, lint), `release.yml` (check, pack, attest, attach) |
