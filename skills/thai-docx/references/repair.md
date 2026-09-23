# Repairing a .docx someone else's program wrote

Read this when the user has a Word file with findings and does not have its content to
rebuild from (SKILL.md, Check an existing .docx).

```sh
python3 scripts/thai_docx repair IN.docx OUT.docx
```

A new file is written; the one given is never touched. Tell the user both paths.

## What this version repairs

| code | what it does |
|---|---|
| `1` | declares compatibility mode 15 — sets the one that is there, drops a second one |
| `2` | marks a run `<w:cs/>` where its text is complex script and takes the mark off where it is not — off the document defaults and the styles too, or a run would only inherit it again; cuts a run that holds both scripts where the script changes. A run that carries a field, a picture, a tab, a break or a numeric character reference is never cut. `--force-cs-whole-doc` marks every run instead and cuts nothing. `--thai-language` also writes `<w:lang w:bidi="th-TH"/>` on the marked runs, and the report says into how many — see [limits.md](limits.md) §3 and §10 |
| `3` | removes `<w:noProof/>`, wherever in the package it is |
| `5` | writes the missing twin of `w:sz`, `w:b` and `w:i`; adds a complex-script font to an `w:rFonts` that names only a Latin one; gives a Symbol bullet a font with Thai in it |
| `order` | puts a run's, a paragraph's and the settings' properties back in the order the schema fixes |

Findings `4` (a word split across two runs) and `invisible` are **reported and left**, in
`remaining`. A file whose only findings are those is not written at all.

**The font.** A run that names no complex-script font is given one: what `--font` says, else the
complex-script font the document already uses most — counting only fonts known to carry Thai —
else this skill's own default. The choice comes back in `warnings`; read it out to the user.

**The file is about the size it was.** The parts this rewrites are compressed again, by a
deflate this project wrote so that both implementations produce the same bytes; a python-docx
file of 36,810 bytes comes back as 39,437. A part is stored instead when compressing would not
make it smaller.

## What it never does

- **It changes no character of the text.** The output's text is compared with the input's, and
  a difference of one character writes nothing (ADR 0023, 0037).
- **It leaves everything else exactly as it was** — every part it did not rewrite keeps its
  bytes, still compressed, with its dates.
- It does not merge runs (code `4`) or remove invisible characters. Beyond the table above it
  does not touch fonts, styles, layout, tracked changes or document properties.
- A file it cannot read — damaged, not a Word file, past the size caps — is refused, as `check`
  refuses it.

## What comes back

```json
{"ok": true, "file": "out.docx",
 "repaired": {"1": 1},
 "remaining": [{"code": "2", "part": "word/document.xml", "message": "…"}],
 "warnings": [], "sha256": "…", "bytes": 24680}
```

Exit 0: repaired, and nothing remains that this version repairs. Exit 1: repaired, and
findings remain — read them out by code from [check.md](check.md). Exit 2: nothing was
written, and `error` says why.

## What to tell the user

- **Setting compatibility mode 15 reflows the document.** Page breaks can move. Say this
  before they send the file to anyone; it is the point of the setting, not a mistake.
- **Rebuilding is still better when they have the content.** A file built from Markdown has
  none of the seven findings; a repaired one has the ones this version cannot reach.
- Give them the new path, and say the original is unchanged.
