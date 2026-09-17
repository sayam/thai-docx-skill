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

## Not proved here

- Building a document in that app: the upload was the question here.
