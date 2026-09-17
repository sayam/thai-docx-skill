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
| the preview | name `thai-docx` and the description as plain text, the repository's address at its end shown but not as a link |
| **Save** | a security scan ran on save; no finding stopped it |
| the skill afterwards | listed under **Created by you**, marked New, switch on, `Contents · 29` — the 29 files of the archive, SKILL.md rendered with License, Compatibility, Author and Version 0.1.1 |

## What changed

- `docs/guide/{en,th}/install.md`: the **tried** row says yes for the Claude apps, and the section
  records what the upload did instead of saying it was not tried.
- The README's install table no longer says "not tried yet" for Claude on the web.

## Not proved here

- Building a document in that app: the upload was the question here.
- Whether any client shows the address in the description as a link; in this preview it is plain
  text.
