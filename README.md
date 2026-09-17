# thai-docx-skill

[![CI](https://img.shields.io/github/actions/workflow/status/sayam/thai-docx-skill/gates.yml?branch=main&label=CI)](https://github.com/sayam/thai-docx-skill/actions/workflows/gates.yml)
[![Release](https://img.shields.io/github/v/release/sayam/thai-docx-skill)](https://github.com/sayam/thai-docx-skill/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/sayam/thai-docx-skill/blob/main/LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/sayam/thai-docx-skill/badge)](https://scorecard.dev/viewer/?uri=github.com/sayam/thai-docx-skill)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14687/badge)](https://www.bestpractices.dev/projects/14687)
[![DOI 10.5281/zenodo.22815936](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.22815936-blue)](https://doi.org/10.5281/zenodo.22815936)

An Agent Skill that makes Word files with Thai text render correctly, in Claude, ChatGPT, Codex, Copilot and more.

**User guide · คู่มือการใช้งาน:** [English](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en.md) · [ภาษาไทย](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/th.md)

Word files with Thai made the usual way go wrong: a red squiggle under every Thai word, lines
that break only at spaces, bold that is not bold, bullets that do not show. With thai-docx, your
AI assistant writes the content as Markdown and one bundled command builds the Word file, with
none of those faults and without changing a character of your text. It is for anyone who writes
Thai documents with an AI assistant, and it also works on its own at the command line.

## Quick start

1. **Download** `thai-docx-0.1.1.zip` from the
   [latest release](https://github.com/sayam/thai-docx-skill/releases/latest).
2. **Install it** in your app:

   | app | do this |
   |---|---|
   | Claude (web, desktop) | turn on code execution, then **Customize > Skills > + > Create skill > Upload a skill** and choose the zip |
   | Claude Code | `mkdir -p ~/.claude/skills && unzip thai-docx-0.1.1.zip -d ~/.claude/skills` |
   | Codex, ChatGPT desktop app | `mkdir -p ~/.agents/skills && unzip thai-docx-0.1.1.zip -d ~/.agents/skills` |
   | ChatGPT Business, Enterprise, Edu | **Plugins > Skills > Create > Upload from your computer** |
   | GitHub Copilot | `mkdir -p ~/.copilot/skills && unzip thai-docx-0.1.1.zip -d ~/.copilot/skills` |
   | Cursor | `mkdir -p ~/.cursor/skills && unzip thai-docx-0.1.1.zip -d ~/.cursor/skills` |
   | Gemini, other agents, the APIs | [step by step for each app](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en/install.md) |

3. **Ask** for a Word file:

   ```text
   Make a Word file in Thai with a short guide to saving water at home
   ```

   You get the file and a note of its settings:

   > Made `water.docx` — TH Sarabun New 16 pt, A4 paper, left margin 1.5 in, other margins 1 in.
   > Any of these can be changed.

## Without an AI

Unzip the release, write `report.md`, and run:

```sh
python3 thai-docx/scripts/thai_docx build report.md report.docx --page-numbers
node thai-docx/scripts/thai_docx.js build report.md report.docx --page-numbers   # the same file
```

Every command: [Use it without an AI](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en/command-line.md).

## What it can do

- Build from a request or from your own Markdown: headings, lists, tables, images, footnotes.
- Change any setting by asking: font, size, paper, margins, line spacing, Thai distributed
  alignment, table of contents, page numbers, headers and footers, Thai digits.
- Ask you the settings first, as multiple choice, when you say `thai-docx grill`.
- Style headings, and lay out a report or thesis: front pages, บทที่ 1, captions, lists of
  tables and figures, ภาคผนวก ก.
- Save settings as a profile, share it as a file, and edit it.
- Check a Thai Word file made by any program and explain what is wrong.

Each one, step by step, with the words to type:
[English guide](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en.md) ·
[คู่มือภาษาไทย](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/th.md)

## Requirements

- Python 3.11 or newer, or Node.js 22 or newer, where the skill runs. Chat apps with code
  execution run Python, though they do not publish its version.
- No internet connection and no packages: the skill needs nothing outside its folder.
- To read the result: the font the file names. The default is TH Sarabun New.

## Status

Version 0.1.1. Files are checked in Word 365 for Windows (the reference), Word for macOS, Google
Docs, LibreOffice Writer and WPS Writer. Changes are listed in
[CHANGELOG.md](https://github.com/sayam/thai-docx-skill/blob/main/CHANGELOG.md).

The OpenSSF Scorecard badge is an automated reading of this repository's settings, workflows and
releases, not of the skill's code or tests. It stays below 10 by design for a project with one
maintainer: no second reviewer, no contributors from other organisations, versions bumped by hand
rather than by a bot, and no score for Maintained until the repository is 90 days old.

## Get help

- A question or a problem: [open an issue](https://github.com/sayam/thai-docx-skill/issues) — first
  see [Fix a problem](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en/troubleshooting.md).
- A security problem: report it privately, as
  [SECURITY.md](https://github.com/sayam/thai-docx-skill/blob/main/.github/SECURITY.md) says.
- Verify a download: `gh attestation verify thai-docx-0.1.1.zip --repo sayam/thai-docx-skill`
  ([how, and how to rebuild it byte for byte](https://github.com/sayam/thai-docx-skill/blob/main/.github/SECURITY.md#verify-a-release)).

## Contributing

Changes are welcome through pull requests. A clone carries the tests, the decision records and the
gates every pull request must pass; how to run them is in
[CONTRIBUTING.md](https://github.com/sayam/thai-docx-skill/blob/main/.github/CONTRIBUTING.md).
Everyone who takes part follows the
[code of conduct](https://github.com/sayam/thai-docx-skill/blob/main/CODE_OF_CONDUCT.md). How the
project is run: [GOVERNANCE.md](https://github.com/sayam/thai-docx-skill/blob/main/GOVERNANCE.md)
and [ROADMAP.md](https://github.com/sayam/thai-docx-skill/blob/main/ROADMAP.md). How it is built
and why it is safe to run: [architecture](https://github.com/sayam/thai-docx-skill/blob/main/docs/architecture.md)
and [assurance case](https://github.com/sayam/thai-docx-skill/blob/main/docs/assurance-case.md).
To cite the skill: archived on Zenodo as
[doi:10.5281/zenodo.22815936](https://doi.org/10.5281/zenodo.22815936), which resolves to the
latest version (each release also gets a DOI of its own); the metadata is in
[CITATION.cff](https://github.com/sayam/thai-docx-skill/blob/main/CITATION.cff).

## License

MIT © 2026 Sayam Sriphua — see [LICENSE](https://github.com/sayam/thai-docx-skill/blob/main/LICENSE). The
verifiable-gates files under `tools/` are Apache-2.0, and the rule texts in `tools/overlay.json`
CC BY 4.0, as `tools/LICENSE` says.
