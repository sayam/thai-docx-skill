# 2026-09-18 — the Claude apps accept the upload

What this proves: `thai-docx-0.1.1.zip`, the archive the release workflow attached, uploads in the
Claude apps on the web, which the guides had marked "not tried". The 200-character limit the Claude
help page gives for a skill's description is what 0.1.0 exceeded (731); 0.1.1's is 195.

Environment: Claude on the web, **Customize > Skills > + > Create skill > Upload a skill**, by the
maintainer on 2026-09-18.

## What happened

| step | result |
|---|---|
| choosing `thai-docx-0.1.1.zip` (583.8 kB) | accepted; the form said a .zip must hold a SKILL.md, and it read this one |
| the preview | name `thai-docx` and the description as plain text, the repository's address at its end not yet a link |
| **Save** | a security scan ran on save; no finding stopped it |
| the skill afterwards | listed under **Created by you**, marked New, switch on, `Contents · 29` — the 29 files of the archive, SKILL.md rendered with License, Compatibility, Author and Version 0.1.1 |

## What changed

- `docs/guide/{en,th}/install.md`: the **tried** row says yes for the Claude apps, and the section
  records what the upload did instead of saying it was not tried.
- The README's install table no longer says "not tried yet" for Claude on the web.

## The skill's page afterwards (claude.ai on the web, same day)

- The description is shown in full, and the repository's address at its end **is** a link there,
  though not in the upload preview.
- There are two **⋮** menus, the same on the web and in the desktop app (checked in both): the one
  in the skills list holds Turn off and Remove; the one on the skill's own page holds Try in chat,
  Edit with Claude, Rename, **Replace**, Duplicate, Download and Remove. `Replace` takes a new zip:
  that is how a reader updates an installed copy, and the guides now say so. `Edit with Claude`
  opens a chat with "Help me edit the thai-docx skill using skill-creator" — an edit in place, not
  a way to install a release.
- The skill also reached this computer through the account's skills sync
  (`~/.claude/skills/synced/…/thai-docx`, version 0.1.1), which is where Claude Code and Cursor
  read it.

## Building a document in the app (same day)

Asked in a chat, with no other instruction than the request, Claude loaded the skill and built the
file. The trace of the turn reads: *Ran skill: thai-docx · Read settings reference and check
runtimes · Generate Thai markdown from artifact data · Build the Thai Word document · Copy the
document to outputs · Shared files*. The reply named the settings the build reports — TH Sarabun
New 16 pt, A4 portrait, margins 1 in with 1.5 in at the left, no table of contents, no page numbers
— and said there were no warnings; the .docx came back in the chat.

The maintainer opened that file in Word 365 for Windows (the reference application, ADR 0012) in a
Windows 10 virtual machine: 27 pages, Thai throughout with no spelling squiggles, headings in
TH Sarabun New at their own size, tables laid out as asked. The document itself is the
maintainer's own work material and is not kept here; what it proves is recorded, not its content
(ADR 0025 §10: this repository carries synthetic content only).

A second run the same day, on **Claude Haiku 4.5** — the smallest model of the family — asked for
the same document "with a first-line indent for paragraphs". The reply reported the settings with
`first-line indent 0.5 นิ้ว` among them, so the model turned the user's words into `--indent 0.5`
and no other flag; the file opened in Word 365 for Windows with the indent on every body paragraph
and the rest as before. The skill is therefore not a large-model-only tool in the app, and the
settings a user asks for in Thai reach the command.

So the guides' **made a file** row says yes for the Claude apps, and the "you get the file:
download it in the chat" cell is now observed rather than read from the documentation.

## Not proved here
